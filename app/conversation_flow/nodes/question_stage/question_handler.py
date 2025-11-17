"""
获取下一个要询问的问题（无需执行大模型）

场景名: information_gathering_question
模板变量：无需执行大模型
执行逻辑：
查询会话下一个要询问的问题，如果没有，返回：action为NONE
有下一个要询问的问题，更新会话问题状态为沟通中，返回：action为SEND_MESSAGE，message为要询问的问题
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import NodeExecutor

logger = structlog.get_logger(__name__)


class QuestionHandlerNode(NodeExecutor):
    """获取下一个要询问的问题（无需LLM）"""

    node_name = "information_gathering_question"
    def __init__(self):
        super().__init__(
            scene_name=self.node_name,
            node_name=self.node_name
        )

    async def _do_execute(self, context: ConversationContext) -> NodeResult:
        """执行节点（获取下一个问题）"""
        from app.services.conversation_question_tracking_service import (
            ConversationQuestionTrackingService
        )
        from app.models.conversation_question_tracking import ConversationQuestionTracking

        tracking_service = ConversationQuestionTrackingService()

        # 查询下一个要询问的问题
        # 性能优化：直接在SQL层过滤pending状态并排序，避免查询所有问题
        next_question: Optional[ConversationQuestionTracking] = await tracking_service.get_next_pending_question(
            conversation_id=context.conversation_id,
            tenant_id=context.tenant_id
        )

        if not next_question:
            # 没有下一个问题
            logger.info("information_gathering_question：no_more_questions_available")
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NONE,
                reason="没有更多问题可询问"
            )

        # # 更新问题状态为ongoing
        # await tracking_service.update_question_status(
        #     tracking_id=next_question.id,
        #     tenant_id=context.tenant_id,
        #     status="ongoing"
        # )

        logger.info(
            "information_gathering_question： next_question_ready",
            question_tracking_id=str(next_question.id),
            question=next_question.question
        )

        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.SEND_MESSAGE, 
            message=next_question.question,
            data={
                "question_tracking_id": str(next_question.id)
            }
        )
