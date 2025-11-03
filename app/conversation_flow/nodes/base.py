"""
节点执行器基类

定义节点执行的通用逻辑和接口
"""
import time
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from opentelemetry import trace

from app.ai.llm.errors import LLMError
from app.conversation_flow.models import NodeResult, ConversationContext
from app.ai import get_llm_caller, LLMCaller

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class NodeExecutor(ABC):
    """节点执行器基类"""

    def __init__(
        self,
        node_name: str,
        scene_name: Optional[str] = None,
        max_retries: int = 3,
        db: Optional[AsyncSession] = None
    ):
        """
        初始化节点执行器

        Args:
            node_name: 节点名称（如 "N1", "N2"）
            scene_name: 场景名称（对应Prompt模板文件名）
            max_retries: 技术异常最大重试次数
            db: 数据库会话（某些节点需要访问数据库）
        """
        self.node_name = node_name
        self.scene_name = scene_name or node_name.lower()
        self.max_retries = max_retries
        self.db = db
        self.llm_caller: Optional[LLMCaller] = None

    async def execute(self, context: ConversationContext) -> NodeResult:
        """
        执行节点（带技术异常重试和性能监控）

        Args:
            context: 会话上下文

        Returns:
            节点执行结果

        Raises:
            LLMError: LLM调用失败（超过重试次数）
            Exception: 其他未预期的异常
        """
        start_time = time.time()

        # 创建span追踪节点执行
        with tracer.start_as_current_span(f"node.{self.node_name}") as span:
            span.set_attribute("node_name", self.node_name)
            span.set_attribute("scene_name", self.scene_name)
            span.set_attribute("conversation_id", str(context.conversation_id))
            span.set_attribute("stage", context.conversation_stage.value)

            logger.info(
                "node_execution_started",
                node_name=self.node_name,
                conversation_id=str(context.conversation_id),
                stage=context.conversation_stage.value
            )

            # 技术异常重试逻辑
            last_exception = None
            for attempt in range(self.max_retries):
                try:
                    result = await self._do_execute(context)

                    # 记录执行耗时
                    execution_time_ms = (time.time() - start_time) * 1000
                    result.execution_time_ms = execution_time_ms

                    # 记录span属性
                    span.set_attribute("action", result.action.value)
                    span.set_attribute("execution_time_ms", round(execution_time_ms, 2))
                    span.set_attribute("attempts", attempt + 1)
                    if result.data.get("fallback"):
                        span.set_attribute("fallback", True)

                    logger.info(
                        "node_execution_completed",
                        node_name=self.node_name,
                        action=result.action.value,
                        execution_time_ms=round(execution_time_ms, 2),
                        attempt=attempt + 1
                    )

                    return result

                except LLMError as e:
                    last_exception = e
                    span.add_event("llm_error", {"attempt": attempt + 1, "error": str(e)})

                    if attempt < self.max_retries - 1:
                        # 指数退避
                        wait_time = 2 ** attempt
                        logger.warning(
                            "node_execution_failed_retrying",
                            node_name=self.node_name,
                            attempt=attempt + 1,
                            max_retries=self.max_retries,
                            wait_time=wait_time,
                            error=str(e)
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            "node_execution_failed_max_retries",
                            node_name=self.node_name,
                            max_retries=self.max_retries,
                            error=str(e)
                        )

                except Exception as e:
                    # 非LLM异常，直接抛出
                    span.set_attribute("error", True)
                    span.record_exception(e)
                    logger.error(
                        "node_execution_failed_unexpected",
                        node_name=self.node_name,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    raise

            # 超过重试次数，返回降级结果
            span.set_attribute("fallback", True)
            span.set_attribute("fallback_reason", "max_retries_exceeded")
            return self._fallback_result(context, last_exception)

    @abstractmethod
    async def _do_execute(self, context: ConversationContext) -> NodeResult:
        """
        执行节点的核心逻辑（子类必须实现）

        Args:
            context: 会话上下文

        Returns:
            节点执行结果
        """
        pass

    async def call_llm(
        self,
        context: ConversationContext,
        scene_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用LLM（CLG1通用逻辑）

        Args:
            context: 会话上下文
            scene_name: 场景名称（默认使用节点的scene_name）
            system_prompt: 系统提示词
            **kwargs: 其他LLM调用参数

        Returns:
            LLM响应结果（已解析为字典）
        """
        # 懒加载LLM调用器
        if self.llm_caller is None:
            self.llm_caller = get_llm_caller()

        # 使用节点的scene_name
        scene_name = scene_name or self.scene_name

        # 获取模板变量
        template_vars = context.get_template_vars()

        # 调用LLM
        return await self.llm_caller.call_with_scene(
            scene_name=scene_name,
            template_vars=template_vars,
            system_prompt=system_prompt,
            **kwargs
        )

    def _fallback_result(
        self,
        context: ConversationContext,
        exception: Optional[Exception] = None
    ) -> NodeResult:
        """
        降级结果（当技术异常超过重试次数时调用）

        默认实现：返回SUSPEND动作（转人工）
        子类应该覆盖此方法提供业务合理的降级逻辑

        Args:
            context: 会话上下文
            exception: 导致降级的异常

        Returns:
            降级的节点执行结果
        """
        from app.conversation_flow.models import NodeAction

        # 记录详细的技术日志（内部使用）
        logger.error(
            "node_fallback_triggered",
            node_name=self.node_name,
            scene_name=self.scene_name,
            conversation_id=str(context.conversation_id),
            error=str(exception) if exception else "unknown",
            error_type=type(exception).__name__ if exception else "unknown"
        )

        # 返回用户友好的消息（可能展示给候选人）
        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.SUSPEND,
            reason="系统繁忙，已转人工客服为您服务",  # 用户友好
            data={
                "fallback": True,
                "fallback_node": self.node_name,
                "internal_error": str(exception) if exception else "unknown"  # 技术细节
            }
        )


class SimpleLLMNode(NodeExecutor):
    """
    简单LLM节点基类

    适用于只调用一次LLM并直接返回结果的节点
    子类只需实现 _parse_llm_response 方法
    """

    async def _do_execute(self, context: ConversationContext) -> NodeResult:
        """执行节点：调用LLM并解析响应"""
        # 调用LLM
        llm_response = await self.call_llm(context)

        # 解析响应
        return await self._parse_llm_response(llm_response, context)

    @abstractmethod
    async def _parse_llm_response(
        self,
        llm_response: Dict[str, Any],
        context: ConversationContext
    ) -> NodeResult:
        """
        解析LLM响应（子类必须实现）

        Args:
            llm_response: LLM响应结果
            context: 会话上下文

        Returns:
            节点执行结果
        """
        pass
