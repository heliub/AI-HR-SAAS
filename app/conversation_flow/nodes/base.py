"""
节点执行器基类

定义节点执行的通用逻辑和接口
"""
import time
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.ai.llm.errors import LLMError
from app.conversation_flow.models import NodeResult, ConversationContext
from app.ai import get_llm_caller, LLMCaller
from app.services.llm_logging_service import get_llm_logging_service
from app.shared.utils.datetime import datetime_now

logger = structlog.get_logger(__name__)


class NodeExecutor(ABC):
    """节点执行器基类"""

    def __init__(
        self,
        node_name: str,
        scene_name: Optional[str] = None,
        max_retries: int = 1,
    ):
        """
        初始化节点执行器

        Args:
            node_name: 节点名称（如 "N1", "N2"）
            scene_name: 场景名称（对应Prompt模板文件名）
            max_retries: 技术异常最大重试次数
        """
        self.node_name = node_name
        self.scene_name = scene_name or node_name.lower()
        self.max_retries = max_retries
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
        started_at = datetime_now()
        error = None
        result = None

        logger.info(
            "node_execution_started",
            node_name=self.node_name,
            conversation_id=str(context.conversation_id),
            stage=context.conversation_stage.value
        )

        # 技术异常重试逻辑
        last_exception = None
        
        try:
            for attempt in range(self.max_retries):
                try:
                    result = await self._do_execute(context)

                    # 记录执行耗时
                    execution_time_ms = datetime_now().timestamp() - started_at.timestamp()
                    result.execution_time_ms = execution_time_ms

                    logger.info(
                        "node_execution_completed",
                        node_name=self.node_name,
                        action=result.action.value,
                        execution_time_ms=round(execution_time_ms, 2),
                        attempt=attempt + 1,
                        result=result
                    )

                    return result

                except LLMError as e:
                    last_exception = e

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
                    # 非LLM异常，记录错误并抛出
                    error = e
                    logger.error(
                        "node_execution_failed_unexpected",
                        node_name=self.node_name,
                        error=str(e),
                        error_type=type(e).__name__,
                        exc_info=True
                    )
                    # raise

            # 超过重试次数，返回降级结果
            result = self._fallback_result(context, last_exception)
            return result
        
        finally:
            # 异步记录节点执行日志
            await self._log_node_execution(context, started_at=started_at, node_result=result, error=error)
    
    async def _log_node_execution(
        self,
        context: ConversationContext,
        started_at: datetime,
        node_result: Optional[NodeResult],
        error: Optional[Exception]
    ) -> None:
        """
        记录节点执行日志（封装方法，不影响主流程可读性）
        
        Args:
            context: 会话上下文
            started_at: 开始时间戳
            node_result: 节点执行结果
            error: 异常对象（如果有）
        """
        try:            
            # 异步记录日志
            logging_service = get_llm_logging_service()
            await logging_service.log_node_execution(
                tenant_id=str(context.tenant_id),
                conversation_id=str(context.conversation_id),
                trigger_message_id=str(context.last_candidate_message_id) if context.last_candidate_message_id else None,
                node_name=self.node_name,
                node_result=node_result,
                started_at=started_at,
                is_success=error is None,
                error_message=str(error) if error else None,
            )
        except Exception as e:
            # 日志记录失败不应影响主流程
            logger.error(
                "node_log_failed",
                node_name=self.node_name,
                error=str(e),
                exc_info=True
            )

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
    ) -> Union[Dict[str, Any], str]:
        """
        调用LLM（CLG1通用逻辑）

        Args:
            context: 会话上下文
            scene_name: 场景名称（默认使用节点的scene_name）
            system_prompt: 系统提示词
            **kwargs: 其他LLM调用参数

        Returns:
            LLM响应结果（parse_json=True时为字典，parse_json=False时为原始字符串）
            类型为Union[Dict[str, Any], str]
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
        exception: Optional[Exception] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> NodeResult:
        """
        降级结果（当技术异常超过重试次数时调用）

        默认实现：返回SUSPEND动作（转人工）
        子类应该覆盖此方法提供业务合理的降级逻辑

        Args:
            context: 会话上下文
            exception: 导致降级的异常
            data: 模型响应结果（可选）

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
            action=NodeAction.NONE,
            reason=None,  # 用户友好
            data=data or {},  # 使用传入的data或空字典
            is_fallback=True,  # 标记为降级结果
            fallback_reason=str(exception) if exception else "技术异常超过重试次数"  # 技术故障原因
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
        llm_response: Union[Dict[str, Any], str],
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
