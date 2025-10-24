"""
Tracing decorators
"""
from functools import wraps
from opentelemetry import trace

from app.core.config import settings


def trace_function(span_name: str = None):
    """函数追踪装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not settings.JAEGER_ENABLED:
                return await func(*args, **kwargs)
            
            tracer = trace.get_tracer(__name__)
            name = span_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("function.result", "success")
                    return result
                except Exception as e:
                    span.set_attribute("function.result", "error")
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator

