"""
会话流程编排器

核心流程控制器，负责：
1. 前置检查（N1+N2并行）
2. Stage路由
3. 组间并行调度（Stage2时）
4. 结果选择策略
"""
import time
import asyncio
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.conversation_flow.models import (
    FlowResult,
    NodeResult,
    ConversationContext,
    NodeAction,
    ConversationStage
)
from app.conversation_flow.node_factory import NodeFactory
from app.conversation_flow.dynamic_executor import DynamicNodeExecutor
from app.conversation_flow.groups.response_group import ResponseGroupExecutor
from app.conversation_flow.groups.question_group import QuestionGroupExecutor
from app.observability.tracing.trace import trace_span
from app.conversation_flow.nodes.precheck.transfer_human import TransferHumanIntentNode
from app.conversation_flow.nodes.precheck.emotion_analysis import EmotionAnalysisNode
from app.conversation_flow.nodes.closing.high_eq import HighEQResponseNode
from app.services.job_question_service import JobQuestionService

logger = structlog.get_logger(__name__)


class ConversationFlowOrchestrator:
    """会话流程编排器"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化流程编排器
        
        Args:
            db: 数据库会话
        """
        self.db = db
        
        # 初始化节点工厂和执行器
        self.factory = NodeFactory(db)
        self.executor = DynamicNodeExecutor(self.factory)
        
        # 初始化组执行器
        self.response_group = ResponseGroupExecutor(self.executor)
        self.question_group = QuestionGroupExecutor(self.executor)
        self.job_question_service = JobQuestionService(db)
    
    async def execute(self, context: ConversationContext) -> FlowResult:
        """
        执行完整流程
        
        Args:
            context: 会话上下文
            
        Returns:
            流程执行结果
        """
        start_time = time.time()
        
        # 创建span追踪整个流程
        with trace_span("conversation_flow.execute"):
            logger.info(
                "flow_execution_started",
                conversation_id=str(context.conversation_id),
                stage=context.conversation_stage.value
            )
            
            try:
                # ============ 阶段1：前置并行检查（N1 + N2） ============
                precheck_result = await self._precheck_phase(context)
                if self.is_break_flow(precheck_result.action) or not precheck_result.next_node:
                    return FlowResult.from_node_result(precheck_result)
                
                if precheck_result.next_node and precheck_result.next_node[0] == HighEQResponseNode.node_name:
                    result = await self.executor.execute(precheck_result.next_node[0], context)
                    return FlowResult.from_node_result(result)
                if await self._should_question_stage(context):
                    question_result = await self.question_group.execute(context)
                    return FlowResult.from_node_result(question_result)
                else:
                    response_result = await self.response_group.execute(context)
                    return FlowResult.from_node_result(response_result)
            except Exception as e:
                logger.error(
                    "flow_execution_failed",
                    conversation_id=str(context.conversation_id),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise
    
    async def _should_question_stage(self, context: ConversationContext) -> bool:
        """
        判断是否应该进入问题询问阶段
        
        Args:
            context: 会话上下文
            
        Returns:
            是否应该进入问题询问阶段
        """
        if context.is_questioning_stage:
            return True
        if not context.is_greeting_stage:
            return False
        job_questions = await self.job_question_service.get_questions_by_job(
            job_id=context.job_id,
            tenant_id=context.tenant_id
        )
        return len(job_questions) > 0

    async def _precheck_phase(
        self,
        context: ConversationContext
    ) -> NodeResult:
        """
        阶段1：前置并行检查（N1 + N2）
        
        并行执行转人工检测和情感分析，并根据结果返回确定性的NodeResult
        
        Args:
            context: 会话上下文
            
        Returns:
            确定性的前置检查结果
        """
        logger.debug("precheck_phase_started")
        
        # 并行执行转人工检测和情感分析
        transfer_task = asyncio.create_task(
            self.executor.execute(TransferHumanIntentNode.node_name, context)
        )
        emotion_task = asyncio.create_task(
            self.executor.execute(EmotionAnalysisNode.node_name, context)
        )
        
        transfer_result, emotion_result = await asyncio.gather(transfer_task, emotion_task)
        if transfer_result.action == NodeAction.SUSPEND:
            return transfer_result
        return emotion_result
    
    def is_break_flow(self, action: NodeAction) -> bool:    
        return action == NodeAction.SUSPEND or action == NodeAction.TERMINATE