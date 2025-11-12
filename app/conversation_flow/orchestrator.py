"""
会话流程编排器

核心流程控制器，负责：
1. 节点并行调度
2. 结果选择策略
3. Stage路由
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
from app.conversation_flow.nodes.precheck import (
    TransferHumanIntentNode,
    EmotionAnalysisNode
)
from app.observability.tracing.trace import trace_span

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

        # 初始化前置检查节点
        self.transfer_human_node = TransferHumanIntentNode()
        self.emotion_analysis_node = EmotionAnalysisNode()

        # 初始化节点组执行器
        from app.conversation_flow.groups import ResponseGroupExecutor, QuestionGroupExecutor
        from app.conversation_flow.nodes.closing import HighEQResponseNode

        self.response_group = ResponseGroupExecutor(db)
        self.question_group = QuestionGroupExecutor(db)
        self.high_eq_node = HighEQResponseNode(db)

        logger.info("conversation_flow_orchestrator_initialized")

    async def execute(self, context: ConversationContext) -> FlowResult:
        """
        执行完整流程

        Args:
            context: 会话上下文

        Returns:
            流程执行结果
        """
        start_time = time.time()
        execution_path = []

        # 创建span追踪整个流程
        with trace_span("conversation_flow.execute"):
            logger.info(
                "flow_execution_started",
                conversation_id=str(context.conversation_id),
                stage=context.conversation_stage.value,
                last_message_length=len(context.last_candidate_message)
            )

            try:
                # ============ 阶段1：前置并行检查 ============
                transfer_human_result, emotion_analysis_result = await self._precheck_phase(context)
                execution_path.extend([transfer_human_result.node_name, emotion_analysis_result.node_name])

                # 短路判断：转人工
                if transfer_human_result.action == NodeAction.SUSPEND:
                    logger.info(
                        "flow_short_circuit",
                        reason="transfer_human_intent",
                        final_action="suspend"
                    )
                    return self._build_flow_result(
                        node_result=transfer_human_result,
                        execution_path=execution_path,
                        start_time=start_time
                    )

                # 短路判断：情感极差
                if emotion_analysis_result.action == NodeAction.SUSPEND:
                    logger.info(
                        "flow_short_circuit",
                        reason="candidate_emotion",
                        final_action="suspend"
                    )
                    return self._build_flow_result(
                        node_result=emotion_analysis_result,
                        execution_path=execution_path,
                        start_time=start_time
                    )

                # 情感一般：发送高情商结束语
                if emotion_analysis_result.data.get("need_closing"):
                    logger.info(
                        "emotion_needs_closing",
                        score=emotion_analysis_result.data.get("emotion_score")
                    )
                    high_eq_result = await self.high_eq_node.execute(context)
                    execution_path.append(high_eq_result.node_name)
                    return self._build_flow_result(
                        node_result=high_eq_result,
                        execution_path=execution_path,
                        start_time=start_time
                    )

                # ============ 阶段2：投机式并行执行 ============
                flow_result = await self._parallel_execution_phase(
                    context,
                    execution_path
                )

                # 记录总耗时
                flow_result.total_time_ms = (time.time() - start_time) * 1000

                logger.info(
                    "flow_execution_completed",
                    conversation_id=str(context.conversation_id),
                    action=flow_result.action.value,
                    total_time_ms=round(flow_result.total_time_ms, 2),
                    execution_path=flow_result.execution_path
                )

                return flow_result

            except Exception as e:
                logger.error(
                    "flow_execution_failed",
                    conversation_id=str(context.conversation_id),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise

    async def _precheck_phase(
        self,
        context: ConversationContext
    ) -> tuple[NodeResult, NodeResult]:
        """
        阶段1：前置并行检查

        Args:
            context: 会话上下文

        Returns:
            (转人工检测结果, 情感分析结果)
        """
        logger.debug("precheck_phase_started")

        # 并行执行转人工检测和情感分析
        transfer_human_task = asyncio.create_task(self.transfer_human_node.execute(context))
        emotion_analysis_task = asyncio.create_task(self.emotion_analysis_node.execute(context))

        transfer_human_result, emotion_analysis_result = await asyncio.gather(transfer_human_task, emotion_analysis_task)

        logger.debug(
            "precheck_phase_completed",
            transfer_human_action=transfer_human_result.action.value,
            emotion_analysis_action=emotion_analysis_result.action.value,
            emotion_score=emotion_analysis_result.data.get("emotion_score")
        )

        return transfer_human_result, emotion_analysis_result

    async def _parallel_execution_phase(
        self,
        context: ConversationContext,
        execution_path: list
    ) -> FlowResult:
        """
        阶段2：投机式并行执行

        根据Stage决定执行策略：
        - questioning(Stage2): 并行执行Response组和Question组，根据结果选择
        - 其他Stage: 只执行Response组

        Args:
            context: 会话上下文
            execution_path: 执行路径（累积）

        Returns:
            流程执行结果
        """
        stage = context.conversation_stage

        logger.debug(
            "parallel_execution_phase_started",
            stage=stage.value
        )

        # 构建并行任务
        tasks = {
            "response": asyncio.create_task(
                self.response_group.execute(context)
            )
        }

        # Stage2时，投机式并行执行问题组
        if stage == ConversationStage.QUESTIONING:
            logger.info("stage2_parallel_execution_response_and_question")
            tasks["question"] = asyncio.create_task(
                self.question_group.execute(context)
            )
        else:
            logger.info("stage1_or_stage3_execute_response_only", stage=stage.value)

        # 等待所有任务完成
        try:
            results = {
                key: result
                for key, result in zip(
                    tasks.keys(),
                    await asyncio.gather(*tasks.values(), return_exceptions=True)
                )
            }
        except Exception as e:
            logger.error(
                "parallel_execution_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise

        # 检查异常
        for key, result in results.items():
            if isinstance(result, Exception):
                logger.error(
                    "parallel_task_failed",
                    task=key,
                    error=str(result),
                    error_type=type(result).__name__
                )
                raise result

        # 结果选择逻辑
        return self._select_result(stage, results, execution_path)

    def _select_result(
        self,
        stage: ConversationStage,
        results: Dict[str, NodeResult],
        execution_path: list
    ) -> FlowResult:
        """
        结果选择策略

        Stage2（questioning）时的优先级：
        1. 问题组有明确动作（SEND_MESSAGE或SUSPEND）-> 使用问题组结果
        2. 对话组有知识库答案（知识库回复成功）-> 使用对话组结果
        3. 问题组返回NONE（进入Stage3）-> 使用对话组结果
        4. 兜底：使用问题组结果

        Stage1/Stage3：直接使用对话组结果

        Args:
            stage: 会话阶段
            results: 执行结果字典
            execution_path: 执行路径

        Returns:
            流程执行结果
        """
        response_result = results["response"]
        question_result = results.get("question")

        # 更新执行路径
        execution_path.append(response_result.node_name)
        if question_result:
            execution_path.append(question_result.node_name)

        logger.debug(
            "result_selection_started",
            stage=stage.value,
            response_action=response_result.action.value,
            question_action=question_result.action.value if question_result else None
        )

        # Stage2：问题阶段 - 复杂的选择逻辑
        if stage == ConversationStage.QUESTIONING:
            # 优先级1：问题组有明确动作（SEND_MESSAGE或SUSPEND）
            if question_result and question_result.action in [
                NodeAction.SEND_MESSAGE,
                NodeAction.SUSPEND
            ]:
                logger.info(
                    "select_question_result_priority_1",
                    action=question_result.action.value
                )
                return FlowResult.from_node_result(question_result)

            # 优先级2：对话组有知识库答案（候选人发问场景）
            if (response_result.node_name == "answer_based_on_knowledge"
                and response_result.action == NodeAction.SEND_MESSAGE):
                logger.info("select_response_result_priority_2_knowledge_answer")
                return FlowResult.from_node_result(response_result)

            # 优先级3：问题组返回NONE（进入Stage3），使用对话组结果
            if question_result and question_result.action == NodeAction.NONE:
                logger.info("select_response_result_priority_3_stage3_transition")
                return FlowResult.from_node_result(response_result)

            # 优先级4：兜底 - 使用问题组结果
            if question_result:
                logger.info("select_question_result_priority_4_fallback")
                return FlowResult.from_node_result(question_result)
            else:
                # 异常情况：Stage2但没有问题组结果
                logger.warning("stage2_but_no_question_result_use_response")
                return FlowResult.from_node_result(response_result)

        # Stage1/Stage3：直接使用对话组结果
        else:
            logger.info("select_response_result_stage1_or_stage3", stage=stage.value)
            return FlowResult.from_node_result(response_result)

    def _build_flow_result(
        self,
        node_result: NodeResult,
        execution_path: list,
        start_time: float
    ) -> FlowResult:
        """
        从节点结果构建流程结果

        Args:
            node_result: 节点执行结果
            execution_path: 执行路径
            start_time: 开始时间

        Returns:
            流程执行结果
        """
        return FlowResult(
            action=node_result.action,
            message=node_result.message,
            reason=node_result.reason,
            execution_path=execution_path,
            metadata={
                "source_node": node_result.node_name,
                "node_data": node_result.data
            },
            total_time_ms=(time.time() - start_time) * 1000
        )
