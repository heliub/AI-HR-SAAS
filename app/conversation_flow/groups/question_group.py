"""
问题阶段处理组执行器

职责：
1. 问题流程编排（基于节点返回的 action 进行流程控制）
2. 问题类型处理（判卷/非判卷）
3. 并行执行优化（封装并行执行逻辑）
4. 数据库查询优化（减少重复操作）
"""
import asyncio
from typing import Optional, Tuple, List
import structlog
from uuid import UUID

from app.conversation_flow.models import Message, NodeResult, ConversationContext, NodeAction, ConversationStage
from app.conversation_flow.nodes.base import NodeExecutor
from app.shared.constants.enums import QuestionType, CandidateMessageRole
from app.models.job_question import JobQuestion
from app.models.conversation_question_tracking import ConversationQuestionTracking
from app.conversation_flow.nodes.question_stage.question_handler import QuestionHandlerNode
from app.conversation_flow.nodes.question_stage.question_willingness import QuestionWillingnessNode
from app.conversation_flow.nodes.question_stage.relevance_check import RelevanceCheckNode
from app.conversation_flow.nodes.question_stage.requirement_match import RequirementMatchNode
from app.services.job_question_service import JobQuestionService
from app.services.conversation_question_tracking_service import ConversationQuestionTrackingService
from app.services.candidate_conversation_service import CandidateConversationService
from app.services.llm_logging_service import get_llm_logging_service
from app.shared.utils.datetime import datetime_now


logger = structlog.get_logger(__name__)


class QuestionGroupExecutor(NodeExecutor):
    node_name = "question_group"
    """
    问题阶段处理组执行器
    """
    
    def __init__(self):
        super().__init__(
            node_name=self.node_name,
            scene_name=self.node_name,
        )
        from app.conversation_flow.dynamic_executor import DynamicNodeExecutor
        self.executor = DynamicNodeExecutor()
        
        # 初始化服务实例，避免重复创建
        self.job_question_service = JobQuestionService()
        self.tracking_service = ConversationQuestionTrackingService()
        self.conversation_service = CandidateConversationService()
    
   
    
    async def _do_execute(self, context: ConversationContext) -> NodeResult:
        """
        执行问题处理流程
        
        流程概览：
        1. 根据会话阶段执行相应处理
        2. Stage1: 初始化问题列表
        3. Stage2: 处理候选人回复并获取下一个问题
        
        Args:
            context: 会话上下文
            
        Returns:
            节点执行结果
        """
        logger.debug(
            "question_flow_started",
            stage=context.conversation_stage.value
        )
        if context.is_greeting_stage:
            return await self._handle_greeting_stage(context)
        if context.is_questioning_stage:
            return await self._handle_questioning_stage(context)
        return NodeResult(node_name="question_group", action=NodeAction.NONE, reason=f"非问题处理阶段（当前Stage: {context.conversation_stage.value}）")
    
    async def _handle_greeting_stage(self, context: ConversationContext) -> NodeResult:
        """
        处理问候阶段（Stage1）
        
        流程：
        1. 检查职位是否有设定的问题并初始化问题列表
        2. 如果没有问题，跳转到Stage3
        3. 如果有问题，跳转到Stage2
        4. 获取第一个问题
        
        Args:
            context: 会话上下文
            
        Returns:
            节点执行结果
        """
        # 合并检查职位问题和初始化问题列表，避免重复查询
        job_questions = await self.job_question_service.get_questions_by_job(
            job_id=context.job_id,
            tenant_id=context.tenant_id
        )
        
        if not job_questions:
            # 没有问题，跳转到Stage3
            await self._update_conversation_stage(context.conversation_id, context.tenant_id, ConversationStage.INTENTION)
            return NodeResult(node_name="QuestionGroup", action=NodeAction.NONE, reason="职位未设定问题，跳转到意向确认阶段")
        
        # 有问题，初始化问题列表
        await self._initialize_question_list(
            context.conversation_id,
            context.job_id,
            context.resume_id,
            context.tenant_id,
            context.user_id,
            job_questions
        )
        
        # 跳转到Stage2
        await self._update_conversation_stage(context.conversation_id, context.tenant_id, ConversationStage.QUESTIONING)
        
        # 获取第一个问题
        return await self._execute_question_handler(context)
    
    async def _handle_questioning_stage(self, context: ConversationContext) -> NodeResult:
        """
        处理询问阶段（Stage2）
        
        流程：
        1. 更新当前问题状态为已完成
        2. 判断当前问题类型（判卷/非判卷）
        3. 根据问题类型执行相应处理
        4. 获取下一个问题
        
        Args:
            context: 会话上下文
            
        Returns:
            节点执行结果
        """
        question_tracking, job_question = await self._get_current_question(context.conversation_id, context.tenant_id)
        if question_tracking is None:
            return await self._execute_question_handler(context)
        same_question_turns_interval = self.same_question_turns_interval(question_tracking.question, context.history)
        if same_question_turns_interval is not None:
            if same_question_turns_interval > 2 and same_question_turns_interval < 5:
                return NodeResult(node_name="QuestionGroup", action=NodeAction.NONE, reason="候选人未发问，跳过问题")
            if same_question_turns_interval >= 5:
                return NodeResult(
                            node_name="QuestionGroup",
                            action=NodeAction.SEND_MESSAGE, 
                            message=question_tracking.question,
                            data={
                                "question_tracking_id": str(question_tracking.id)
                            }
                        )
        
        context.current_question_id = question_tracking.question_id
        context.current_question_content = question_tracking.question
        context.current_question_requirement = job_question.evaluation_criteria
        # 根据问题类型执行相应处理
        if job_question.question_type == QuestionType.ASSESSMENT and job_question.is_required:
            # 判卷问题：执行并行检查
            node_result = await self._execute_parallel_question_checks(context)
        else:
            # 非判卷问题：执行沟通意愿检查
            node_result = await self.executor.execute(QuestionWillingnessNode.node_name, context)
        
        await self.process_question_status(node_result, question_tracking.id, context.tenant_id)
        
        next_node = node_result
        while (next_node and next_node.action == NodeAction.NEXT_NODE):
            next_node = await self.executor.execute(next_node.next_node[0], context)
        return next_node

    def same_question_turns_interval(self, question: str, history: List[Message]) -> Optional[int]:
        if not history:
            return None
        talk_turns = 0
        current_role = None
        last_msg_role = None
        for msg in reversed(history):
            if current_role is None:
                current_role = msg.sender
                last_msg_role = msg.sender
                talk_turns += 1
            if msg.sender != current_role:
                current_role = msg.sender
                if msg.sender == last_msg_role:
                    talk_turns += 1
            if msg.sender == CandidateMessageRole.HR and question in msg.content:
                return talk_turns
            if talk_turns > 5:
                break
        return None


    async def process_question_status(self, node_result: NodeResult, question_tracking_id: UUID, tenant_id: UUID) -> None:
        """
        处理问题状态
        
        Args:
            node_result: 节点执行结果
            question_tracking_id: 问题跟踪ID
            tenant_id: 租户ID
        """
        if node_result.node_name == QuestionWillingnessNode.node_name:
            return await self._complete_current_question(question_tracking_id, tenant_id, None)
            
        if node_result.node_name == RequirementMatchNode.node_name:
            match_result = node_result.data.get("is_satisfied", None) if node_result.data and isinstance(node_result.data, dict) else None
            if match_result is not None:
                return await self._complete_current_question(question_tracking_id, tenant_id, match_result)
        return None

    async def _execute_parallel_question_checks(self, context: ConversationContext) -> NodeResult:
        """
        并行执行问题检查（判卷问题）
        
        封装并行执行逻辑，统一处理并行结果
        
        Args:
            context: 会话上下文
            
        Returns:
            处理结果
        """

        relevance_task = asyncio.create_task(
            self.executor.execute(RelevanceCheckNode.node_name, context)
        )
        requirement_task = asyncio.create_task(
            self.executor.execute(RequirementMatchNode.node_name, context)
        )
        relevance_result, requirement_result = await asyncio.gather(relevance_task, requirement_task, return_exceptions=True)
        if relevance_result.next_node and relevance_result.next_node[0] == RequirementMatchNode.node_name:
            return requirement_result
        return relevance_result

    async def _get_current_question(self, conversation_id: UUID, tenant_id: UUID) -> Tuple[Optional[ConversationQuestionTracking], Optional[JobQuestion]]:
        """
        获取当前问题类型
        
        Args:
            conversation_id: 会话ID
            tenant_id: 租户ID
            
        Returns:
            问题类型
        """
         # 先查询 ongoing 状态的问题
        current_questions = await self.tracking_service.get_questions_by_conversation(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            status="ongoing"
        )
        
        if not current_questions or len(current_questions) == 0:
            return None, None
        
        # 查询原始问题以判断类型
        raw_question = await self.job_question_service.get_by_id(JobQuestion, current_questions[0].question_id, tenant_id)
        return current_questions[0], raw_question
            
    async def _initialize_question_list(
        self,
        conversation_id: UUID,
        job_id: UUID,
        resume_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
        job_questions: List
    ) -> None:
        """
        使用已查询的问题列表初始化问题跟踪
        
        Args:
            conversation_id: 会话ID
            job_id: 职位ID
            resume_id: 简历ID
            tenant_id: 租户ID
            user_id: 用户ID
            job_questions: 已查询的职位问题列表
        """
        # 批量创建问题跟踪记录
        await self.tracking_service.bulk_create_question_tracking(
            conversation_id=conversation_id,
            job_id=job_id,
            resume_id=resume_id,
            tenant_id=tenant_id,
            user_id=user_id,
            job_questions=job_questions
        )
    
    async def _update_conversation_stage(self, conversation_id: UUID, tenant_id: UUID, stage: str) -> None:
        """
        更新会话阶段（合并了原来的两个方法）
        
        Args:
            conversation_id: 会话ID
            tenant_id: 租户ID
            stage: 目标阶段
        """
        await self.conversation_service.update_conversation_stage(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            stage=stage
        )
    
    async def _complete_current_question(self, tracking_id: UUID, tenant_id: UUID, is_satisfied: Optional[bool] = None) -> None:
        """
        完成当前问题（更新状态为已完成）
        
        Args:
            tracking_id: 跟踪ID
            tenant_id: 租户ID
            is_satisfied: 是否满足要求
        """
        await self.tracking_service.update_question_status(
            tracking_id=tracking_id,
            tenant_id=tenant_id,
            status="completed",
            is_satisfied=is_satisfied
        )
        
        logger.info("current_question_completed", question_id=str(tracking_id))
    
    
    async def _execute_question_handler(self, context: ConversationContext) -> NodeResult:
        """
        执行问题处理器获取下一个问题
        
        Args:
            context: 会话上下文
            
        Returns:
            节点执行结果
        """
        # 执行问题处理器获取下一个问题
        node_result = await self.executor.execute(QuestionHandlerNode.node_name, context)
        if node_result.action == NodeAction.NONE:
            await self._update_conversation_stage(context.conversation_id, context.tenant_id, ConversationStage.INTENTION)
        return node_result