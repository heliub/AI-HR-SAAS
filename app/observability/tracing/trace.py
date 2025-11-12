"""
轻量级Trace实现

提供基础的span追踪功能，替代OpenTelemetry
"""
import time
from dataclasses import dataclass, field
from typing import Optional
from contextlib import contextmanager
import structlog

from app.observability import context

logger = structlog.get_logger(__name__)


@dataclass
class Span:
    """轻量级Span"""
    
    name: str
    span_id: str
    trace_id: str
    parent_span_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    @property
    def duration_ms(self) -> float:
        """计算持续时间（毫秒）"""
        end = self.end_time if self.end_time else time.time()
        return (end - self.start_time) * 1000
    
    def finish(self) -> None:
        """结束span"""
        self.end_time = time.time()


@contextmanager
def trace_span(name: str, log_span: bool = True):
    """
    创建span上下文管理器
    
    Args:
        name: span名称
        log_span: 是否记录span日志
        
    Yields:
        Span: span对象
    """
    # 获取或创建trace_id
    trace_id = context.get_trace_id()
    if not trace_id:
        trace_id = context.new_trace_id()
    # 保存父span_id
    parent_span_id = context.get_span_id()
    # 创建新span
    span_id = context.new_span_id()
    context.set_parent_span_id(parent_span_id)
    
    span = Span(
        name=name,
        span_id=span_id,
        trace_id=trace_id,
        parent_span_id=parent_span_id
    )
    
    # 绑定到structlog context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        trace_id=trace_id,
        span_id=span_id
    )
    if parent_span_id:
        structlog.contextvars.bind_contextvars(parent_span_id=parent_span_id)
    try:
        yield span
    finally:
        span.finish()
        # 恢复父span
        if parent_span_id:
            context.set_span_id(parent_span_id)

