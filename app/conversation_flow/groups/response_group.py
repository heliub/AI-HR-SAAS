"""
对话回复组执行器

组合节点：沟通意愿判断 -> 发问检测 -> 知识库回复/兜底回复/闲聊 -> 高情商回复(可选)
投机式并行：发问检测 + 知识库回复 同时执行，根据发问检测结果选择使用哪个
"""
import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.response import (
    ContinueConversationNode,
    AskQuestionNode,
    KnowledgeAnswerNode,
    FallbackAnswerNode,
    CasualChatNode,
)
from app.conversation_flow.nodes.closing import HighEQResponseNode

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
        self.continue_conversation_node = ContinueConversationNode()
        self.ask_question_node = AskQuestionNode()
        self.knowledge_answer_node = KnowledgeAnswerNode(db)
        self.fallback_answer_node = FallbackAnswerNode()
        self.casual_chat_node = CasualChatNode()
        self.high_eq_node = HighEQResponseNode(db)

        logger.info("response_group_executor_initialized")

    async def execute(self, context: ConversationContext) -> NodeResult:
        """
        执行对话回复链

        执行流程：
        1. 根据Stage决定是否执行沟通意愿判断
        2. 并行执行发问检测和知识库回复（投机式优化）
        3. 根据发问检测结果选择回复策略

        Args:
            context: 会话上下文

        Returns:
            节点执行结果
        """
        logger.debug(
            "response_group_execution_started",
            stage=context.conversation_stage.value
        )

        # ========== Step1: 执行沟通意愿判断（条件性） ==========
        # Stage2(questioning)和Stage3(intention)跳过沟通意愿判断
        if context.is_questioning_stage or context.is_intention_stage:
            logger.debug("skip_continue_conversation_for_stage", stage=context.conversation_stage.value)
            continue_conversation_result = NodeResult(
                node_name="continue_conversation_with_candidate",
                action=NodeAction.CONTINUE,
                data={"willing": True, "skipped": True}
            )
        else:
            # Stage1(greeting)执行沟通意愿判断
            continue_conversation_result = await self.continue_conversation_node.execute(context)

        # 沟通意愿判断：不愿意沟通 -> 发送高情商结束语
        if not continue_conversation_result.data.get("willing"):
            logger.info("candidate_unwilling_send_closing")
            return await self.high_eq_node.execute(context)

        # ========== Step2: 并行执行发问检测和知识库回复（投机式优化） ==========
        logger.debug("parallel_execution_ask_question_knowledge_answer_started")

        ask_question_task = asyncio.create_task(self.ask_question_node.execute(context))
        knowledge_answer_task = asyncio.create_task(self.knowledge_answer_node.execute(context))

        ask_question_result, knowledge_answer_result = await asyncio.gather(ask_question_task, knowledge_answer_task)

        logger.debug(
            "parallel_execution_ask_question_knowledge_answer_completed",
            is_question=ask_question_result.data.get("is_question"),
            knowledge_found=knowledge_answer_result.data.get("found")
        )

        # ========== Step3: 根据发问检测结果选择回复策略 ==========
        if ask_question_result.data.get("is_question"):
            # 候选人发问了
            if (knowledge_answer_result.node_name == "answer_based_on_knowledge"
                and knowledge_answer_result.action == NodeAction.SEND_MESSAGE):
                # 知识库有答案，使用知识库回复结果
                logger.info("use_knowledge_answer")
                return knowledge_answer_result
            else:
                # 知识库无答案，使用兜底回复
                logger.info("use_fallback_answer")
                return await self.fallback_answer_node.execute(context)
        else:
            # 候选人未发问，执行闲聊
            logger.info("use_casual_chat")
            return await self.casual_chat_node.execute(context)
