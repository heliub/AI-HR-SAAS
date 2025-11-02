"""
对话回复组执行器

组合节点：N3 -> N4 -> N9/N10/N11 -> N12(可选)
投机式并行：N4 + N9 同时执行，根据N4结果选择使用哪个
"""
import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.response import (
    N3ContinueConversationNode,
    N4AskQuestionNode,
    N9KnowledgeAnswerNode,
    N10FallbackAnswerNode,
    N11CasualChatNode,
)
from app.conversation_flow.nodes.closing import N12HighEQResponseNode

logger = structlog.get_logger(__name__)


class ResponseGroupExecutor:
    """对话回复组执行器（N3->N4->N9/N10/N11）"""

    def __init__(self, db: AsyncSession):
        """
        初始化对话回复组执行器

        Args:
            db: 数据库会话
        """
        self.db = db
        self.n3 = N3ContinueConversationNode()
        self.n4 = N4AskQuestionNode()
        self.n9 = N9KnowledgeAnswerNode(db)
        self.n10 = N10FallbackAnswerNode()
        self.n11 = N11CasualChatNode()
        self.n12 = N12HighEQResponseNode(db)

        logger.info("response_group_executor_initialized")

    async def execute(self, context: ConversationContext) -> NodeResult:
        """
        执行对话回复链

        执行流程：
        1. 根据Stage决定是否执行N3
        2. 并行执行N4和N9（投机式优化）
        3. 根据N4结果选择使用N9/N10/N11

        Args:
            context: 会话上下文

        Returns:
            节点执行结果
        """
        logger.debug(
            "response_group_execution_started",
            stage=context.conversation_stage.value
        )

        # ========== Step1: 执行N3（条件性） ==========
        # Stage2(questioning)和Stage3(intention)跳过N3
        if context.is_questioning_stage or context.is_intention_stage:
            logger.debug("skip_n3_for_stage", stage=context.conversation_stage.value)
            n3_result = NodeResult(
                node_name="N3",
                action=NodeAction.CONTINUE,
                data={"willing": True, "skipped": True}
            )
        else:
            # Stage1(greeting)执行N3
            n3_result = await self.n3.execute(context)

        # N3判断：不愿意沟通 -> 发送N12高情商结束语
        if not n3_result.data.get("willing"):
            logger.info("candidate_unwilling_send_closing")
            return await self.n12.execute(context)

        # ========== Step2: 并行执行N4和N9（投机式优化） ==========
        logger.debug("parallel_execution_n4_n9_started")

        n4_task = asyncio.create_task(self.n4.execute(context))
        n9_task = asyncio.create_task(self.n9.execute(context))

        n4_result, n9_result = await asyncio.gather(n4_task, n9_task)

        logger.debug(
            "parallel_execution_n4_n9_completed",
            is_question=n4_result.data.get("is_question"),
            knowledge_found=n9_result.data.get("found")
        )

        # ========== Step3: 根据N4结果选择回复策略 ==========
        if n4_result.data.get("is_question"):
            # 候选人发问了
            if n9_result.action == NodeAction.SEND_MESSAGE:
                # 知识库有答案，使用N9结果
                logger.info("use_knowledge_answer")
                return n9_result
            else:
                # 知识库无答案，使用N10兜底回复
                logger.info("use_fallback_answer")
                return await self.n10.execute(context)
        else:
            # 候选人未发问，执行N11闲聊
            logger.info("use_casual_chat")
            return await self.n11.execute(context)
