"""
LLM日志记录服务

提供异步的LLM执行日志和对话流程节点执行日志记录功能
"""
import asyncio
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any
import structlog

from app.models.llm_execution_log import LLMExecutionLog
from app.models.conversation_flow_node_execution_log import ConversationFlowNodeExecutionLog
from app.infrastructure.database.session import get_db_context
from app.shared.utils.datetime import datetime_now
from app.observability import context as trace_context
from app.conversation_flow.models import NodeResult

logger = structlog.get_logger(__name__)


class LLMLoggingService:
    """LLM日志记录服务（简化版：直接异步保存）"""
    
    async def log_llm_execution(
        self,
        scene_name: Optional[str],
        provider: Optional[str],
        model: Optional[str],
        temperature: Optional[float],
        top_p: Optional[float],
        max_completion_tokens: Optional[int],
        template_variables: Optional[Dict[str, Any]],
        response_content: Optional[str],
        prompt_tokens: Optional[int],
        completion_tokens: Optional[int],
        total_tokens: Optional[int],
        started_at: Optional[datetime],
        is_success: bool = True,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        异步记录LLM执行日志（直接保存到数据库）
        
        Args:
            trace_id: 流程追踪ID
            scene_name: 场景名称
            provider: LLM提供商
            model: 模型名称
            temperature: 温度参数
            top_p: top_p参数
            max_completion_tokens: 最大完成token数
            template_variables: 模板变量（字典）
            response_content: 响应内容
            prompt_tokens: Prompt token数
            completion_tokens: 完成token数
            total_tokens: 总token数
            started_at: 开始时间
            completed_at: 完成时间
            execution_time_ms: 执行耗时
            is_success: 是否成功
            error_type: 错误类型
            error_message: 错误信息
        """
        # 创建异步任务，不阻塞主流程
        asyncio.create_task(self._save_llm_log(
            trace_id=trace_context.get_trace_id(),
            scene_name=scene_name,
            provider=provider,
            model=model,
            temperature=temperature,
            top_p=top_p,
            max_completion_tokens=max_completion_tokens,
            template_variables=template_variables,
            response_content=response_content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            started_at=started_at,
            is_success=is_success,
            error_type=error_type,
            error_message=error_message,
        ))
    
    async def _save_llm_log(
        self,
        trace_id: Optional[str],
        scene_name: Optional[str],
        provider: Optional[str],
        model: Optional[str],
        temperature: Optional[float],
        top_p: Optional[float],
        max_completion_tokens: Optional[int],
        template_variables: Optional[Dict[str, Any]],
        response_content: Optional[str],
        prompt_tokens: Optional[int],
        completion_tokens: Optional[int],
        total_tokens: Optional[int],
        started_at: datetime,
        is_success: bool,
        error_type: Optional[str],
        error_message: Optional[str],
    ) -> None:
        """保存LLM日志到数据库"""
        try:
            # 如果没有传completed_at，使用当前时间
            completed_at = datetime_now()
            execution_time_ms = (completed_at - started_at).total_seconds() * 1000 if started_at else None
            
            async with get_db_context() as db:
                log = LLMExecutionLog(
                    tenant_id=None,  # LLM日志不记录租户ID
                    trace_id=trace_id,
                    scene_name=scene_name,
                    provider=provider,
                    model=model,
                    temperature=temperature,
                    top_p=top_p,
                    max_completion_tokens=max_completion_tokens,
                    template_variables=json.dumps(template_variables, ensure_ascii=False) if template_variables else None,
                    response_content=response_content,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    started_at=started_at,
                    completed_at=completed_at,
                    execution_time_ms=execution_time_ms,
                    is_success=is_success,
                    error_type=error_type,
                    error_message=error_message,
                )
                db.add(log)
                await db.commit()
        except Exception as e:
            logger.error(
                "llm_log_save_failed",
                scene_name=scene_name,
                error=str(e),
                exc_info=True
            )
    
    async def log_node_execution(
        self,
        tenant_id: str,
        conversation_id: str,
        trigger_message_id: Optional[str],
        node_name: str,
        node_result: Optional[NodeResult],
        started_at: datetime,
        is_success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """
        异步记录节点执行日志（直接保存到数据库）
        
        Args:
            tenant_id: 租户ID
            trace_id: 流程追踪ID
            conversation_id: 会话ID
            trigger_message_id: 触发消息ID
            node_name: 节点名称
            node_result: 节点结果（字典）
            started_at: 开始时间
            is_success: 是否成功
            error_message: 错误信息
        """
        # 创建异步任务，不阻塞主流程
        asyncio.create_task(self._save_node_log(
            tenant_id=tenant_id,
            trace_id=trace_context.get_trace_id(),
            conversation_id=conversation_id,
            trigger_message_id=trigger_message_id,
            node_name=node_name,
            node_result=node_result,
            started_at=started_at,
            is_success=is_success,
            error_message=error_message,
        ))
    
    async def _save_node_log(
        self,
        tenant_id: str,
        trace_id: Optional[str],
        conversation_id: str,
        trigger_message_id: Optional[str],
        node_name: str,
        node_result: Optional[NodeResult],
        started_at: datetime,
        is_success: bool,
        error_message: Optional[str],
    ) -> None:
        """保存节点日志到数据库"""
        try:
            completed_at = datetime_now()
            execution_time_ms = (completed_at - started_at).total_seconds() * 1000 if started_at else None
            async with get_db_context() as db:
                log = ConversationFlowNodeExecutionLog(
                    tenant_id=tenant_id,
                    trace_id=trace_id,
                    conversation_id=conversation_id,
                    trigger_message_id=trigger_message_id,
                    node_name=node_name,
                    node_result=node_result.model_dump_json(ensure_ascii=False) if node_result else None,
                    llm_execution_id=None,
                    started_at=started_at,
                    completed_at=completed_at,
                    execution_time_ms=execution_time_ms,
                    is_success=is_success,
                    error_message=error_message,
                )
                db.add(log)
                await db.commit()
        except Exception as e:
            logger.error(
                "node_log_save_failed",
                node_name=node_name,
                error=str(e),
                exc_info=True
            )


# 全局单例
_logging_service: Optional[LLMLoggingService] = None


def get_llm_logging_service() -> LLMLoggingService:
    """获取LLM日志服务单例"""
    global _logging_service
    if _logging_service is None:
        _logging_service = LLMLoggingService()
    return _logging_service

