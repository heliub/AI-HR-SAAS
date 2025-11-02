"""
HR询问的问题处理（无需执行大模型）

场景名: information_gathering_question
模板变量：无需执行大模型
执行逻辑：
step1.如果当前会话处于Stage1，查询职位设定的要询问的问题，如果没有设定问题，更新会话阶段为Stage3对应的状态值；
      如果有问题，则初始化职位问题到当前会话问题中，同时设定会话阶段为Stage2对应的状态值，并执行step3
step2.如果当前会话处于Stage2，查询当前会话正在询问的问题，更新状态为完成
step3.查询会话下一个要询问的问题，如果没有，更新会话阶段为state3对应的状态值，返回：action为NONE
      有下一个要询问的问题，更新会话问题状态为沟通中，返回：action为SEND_MESSAGE，message为要询问的问题
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import NodeExecutor

logger = structlog.get_logger(__name__)


class QuestionHandlerNode(NodeExecutor):
    """HR询问的问题处理（无需LLM）"""

    def __init__(self, db: AsyncSession):
        super().__init__(
            scene_name="information_gathering_question",
            node_name="information_gathering_question",
            db=db
        )

    async def _do_execute(self, context: ConversationContext) -> NodeResult:
        """执行节点（直接操作数据库）"""
        from app.services.job_question_service import JobQuestionService
        from app.services.conversation_question_tracking_service import (
            ConversationQuestionTrackingService
        )
        from app.services.candidate_conversation_service import (
            CandidateConversationService
        )
        from app.models.job_question import JobQuestion
        from app.models.conversation_question_tracking import ConversationQuestionTracking

        job_question_service = JobQuestionService(self.db)
        tracking_service = ConversationQuestionTrackingService(self.db)
        conversation_service = CandidateConversationService(self.db)

        # ========== Step1: Stage1处理 - 初始化问题 ==========
        if context.is_greeting_stage:
            logger.info(
                "question_handler_stage1_init_questions",
                conversation_id=str(context.conversation_id)
            )

            # 查询职位设定的问题
            job_questions: List[JobQuestion] = await job_question_service.get_questions_by_job(
                job_id=context.job_id,
                tenant_id=context.tenant_id
            )

            if not job_questions:
                # 无问题，直接跳Stage3
                logger.info("no_questions_skip_to_stage3")
                await conversation_service.update_conversation_stage(
                    conversation_id=context.conversation_id,
                    tenant_id=context.tenant_id,
                    stage="intention"  # Stage3
                )

                return NodeResult(
                    node_name=self.node_name,
                    action=NodeAction.NONE,
                    reason="无职位问题，跳转到Stage3"
                )

            # 初始化问题到会话
            logger.info("init_questions_to_conversation", count=len(job_questions))

            for question in job_questions:
                await tracking_service.create_question_tracking(
                    conversation_id=context.conversation_id,
                    question_id=question.id,
                    job_id=context.job_id,
                    resume_id=context.resume_id,
                    question=question.question,
                    tenant_id=context.tenant_id,
                    user_id=context.user_id,
                    tracking_data={"status": "pending"}
                )

            # 更新Stage为questioning(Stage2)
            await conversation_service.update_conversation_stage(
                conversation_id=context.conversation_id,
                tenant_id=context.tenant_id,
                stage="questioning"  # Stage2
            )

            # 继续执行Step3
            logger.debug("continue_to_step3_after_init")

        # ========== Step2: Stage2处理 - 更新当前问题状态 ==========
        elif context.is_questioning_stage:
            logger.debug(
                "question_handler_stage2_update_current_question",
                current_question_id=str(context.current_question_id) if context.current_question_id else None
            )

            if context.current_question_id:
                # 更新当前问题状态为completed
                await tracking_service.update_question_status(
                    tracking_id=context.current_question_id,
                    tenant_id=context.tenant_id,
                    status="completed"
                )

                logger.info("current_question_marked_completed")

        # ========== Step3: 查询下一个要询问的问题 ==========
        # 性能优化：直接在SQL层过滤pending状态并排序，避免查询所有问题
        next_question: Optional[ConversationQuestionTracking] = await tracking_service.get_next_pending_question(
            conversation_id=context.conversation_id,
            tenant_id=context.tenant_id
        )

        if not next_question:
            # 没有下一个问题，更新Stage为intention(Stage3)
            logger.info("no_more_questions_move_to_stage3")

            await conversation_service.update_conversation_stage(
                conversation_id=context.conversation_id,
                tenant_id=context.tenant_id,
                stage="intention"  # Stage3
            )

            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NONE,
                reason="所有问题已询问完毕，进入Stage3"
            )

        # 更新问题状态为ongoing
        await tracking_service.update_question_status(
            tracking_id=next_question.id,
            tenant_id=context.tenant_id,
            status="ongoing"
        )

        logger.info(
            "next_question_ready",
            question_id=str(next_question.id),
            question_preview=next_question.question[:50]
        )

        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.SEND_MESSAGE,
            message=next_question.question,
            data={
                "question_id": str(next_question.id),
                "question_type": next_question.question_id  # 关联原始问题ID
            }
        )
