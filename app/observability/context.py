"""
统一Context管理

基于contextvars实现的trace上下文管理，支持trace_id和span_id的传递
"""
from contextvars import ContextVar
from typing import Optional
import uuid

# Context variables
_trace_id: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
_span_id: ContextVar[Optional[str]] = ContextVar('span_id', default=None)
_parent_span_id: ContextVar[Optional[str]] = ContextVar('parent_span_id', default=None)


def get_trace_id() -> Optional[str]:
    """获取当前trace_id"""
    return _trace_id.get()


def set_trace_id(trace_id: str) -> None:
    """设置trace_id"""
    _trace_id.set(trace_id)


def new_trace_id() -> str:
    """生成新的trace_id"""
    trace_id = str(uuid.uuid4())
    set_trace_id(trace_id)
    return trace_id


def get_span_id() -> Optional[str]:
    """获取当前span_id"""
    return _span_id.get()


def set_span_id(span_id: str) -> None:
    """设置span_id"""
    _span_id.set(span_id)


def new_span_id() -> str:
    """生成新的span_id（使用短ID）"""
    span_id = str(uuid.uuid4())[:8]
    set_span_id(span_id)
    return span_id


def get_parent_span_id() -> Optional[str]:
    """获取父span_id"""
    return _parent_span_id.get()


def set_parent_span_id(span_id: Optional[str]) -> None:
    """设置父span_id"""
    _parent_span_id.set(span_id)


def clear_context() -> None:
    """清空所有上下文（测试时使用）"""
    _trace_id.set(None)
    _span_id.set(None)
    _parent_span_id.set(None)

