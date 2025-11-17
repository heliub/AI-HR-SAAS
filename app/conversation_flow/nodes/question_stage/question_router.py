"""
问题询问阶段处理（复合节点，无需LLM）

前置条件：Stage1且职位存在有效的设定问题，或者Stage2
场景名：information_gathering
模板变量：无需执行大模型
执行逻辑：
1.如果是Stage1，且职位未设定有效的问题，action:NONE
  否则：action:NEXT_NODE, next_node:information_gathering_question
2.如果是Stage2，如果当前问题属于判卷问题，action:NEXT_NODE, next_node:relevance_reply_and_question
  否则：action:NEXT_NODE, next_node:candidate_communication_willingness_for_question
3.如果是其他Stage，action:NONE
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import NodeExecutor

logger = structlog.get_logger(__name__)


class QuestionRouterNode(NodeExecutor):
    """问题询问阶段处理（路由节点，无需LLM）"""

    node_name = "information_gathering"
    def __init__(self):
        super().__init__(
            scene_name=self.node_name,
            node_name=self.node_name
        )

    async def _do_execute(self, context: ConversationContext) -> NodeResult:
        """执行节点（路由逻辑）"""
        from app.services.job_question_service import JobQuestionService
        from app.services.conversation_question_tracking_service import (
            ConversationQuestionTrackingService
        )

        # ========== 1. Stage1处理 ==========
        if context.is_greeting_stage:
            # 查询职位是否有有效的问题
            job_question_service = JobQuestionService()
            questions = await job_question_service.get_questions_by_job(
                job_id=context.job_id,
                tenant_id=context.tenant_id
            )

            if not questions:
                # 职位未设定有效的问题
                logger.info("question_router_stage1_no_questions")
                return NodeResult(
                    node_name=self.node_name,
                    action=NodeAction.NONE,
                    reason="职位未设定问题"
                )
            else:
                # 有问题，路由到问题处理初始化
                logger.info("question_router_stage1_has_questions_route_to_question_handler")
                return NodeResult(
                    node_name=self.node_name,
                    action=NodeAction.NEXT_NODE,
                    next_node=["information_gathering_question"],
                    reason="职位有问题，初始化问题列表"
                )

        # ========== 2. Stage2处理 ==========
        elif context.is_questioning_stage:
            logger.debug("question_router_stage2_check_question_type")

            # 获取当前正在询问的问题
            tracking_service = ConversationQuestionTrackingService()
            questions = await tracking_service.get_questions_by_conversation(
                conversation_id=context.conversation_id,
                tenant_id=context.tenant_id
            )

            # 找到ongoing状态的问题
            current_question = next(
                (q for q in questions if q.status == "ongoing"),
                None
            )

            if not current_question:
                logger.warning("question_router_stage2_no_ongoing_question")
                return NodeResult(
                    node_name=self.node_name,
                    action=NodeAction.NONE,
                    reason="Stage2但没有正在进行的问题"
                )

            # 查询原始问题以判断类型
            from app.services.job_question_service import JobQuestionService
            job_question_service = JobQuestionService()

            # 通过question_id查询原始JobQuestion
            from app.models.job_question import JobQuestion
            job_question = await job_question_service.get_by_id(
                JobQuestion,
                current_question.question_id,
                context.tenant_id
            )

            if not job_question:
                logger.warning(
                    "question_router_stage2_job_question_not_found",
                    question_id=str(current_question.question_id)
                )
                # 默认当作非判卷问题
                return NodeResult(
                    node_name=self.node_name,
                    action=NodeAction.NEXT_NODE,
                    next_node=["information_gathering_question"],
                    reason="找不到原始问题，默认非判卷"
                )

            # 判断问题类型
            # question_type: "information"-信息采集, "assessment"-考察评估（判卷）
            is_scoring = job_question.question_type == "assessment"

            logger.info(
                "question_router_stage2_question_type_determined",
                question_type=job_question.question_type,
                is_scoring=is_scoring
            )

            if is_scoring:
                # 判卷问题：路由到相关性检查
                return NodeResult(
                    node_name=self.node_name,
                    action=NodeAction.NEXT_NODE,
                    next_node=["relevance_reply_and_question"],
                    reason="判卷问题，检查相关性",
                    data={"question_type": "assessment", "is_scoring": True}
                )
            else:
                # 非判卷问题：路由到沟通意愿检查
                return NodeResult(
                    node_name=self.node_name,
                    action=NodeAction.NEXT_NODE,
                    next_node=["candidate_communication_willingness_for_question"],
                    reason="非判卷问题，检查沟通意愿",
                    data={"question_type": "information", "is_scoring": False}
                )

        # ========== 3. 其他Stage ==========
        else:
            logger.debug("question_router_other_stage_skip", stage=context.conversation_stage.value)
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NONE,
                reason=f"非Stage1/2，跳过问题处理（当前Stage: {context.conversation_stage.value}）"
            )
