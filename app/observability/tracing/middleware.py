"""
Tracing middleware
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from opentelemetry import trace

from app.core.config import settings


class TracingMiddleware(BaseHTTPMiddleware):
    """追踪中间件"""
    
    async def dispatch(self, request: Request, call_next):
        if not settings.JAEGER_ENABLED:
            return await call_next(request)
        
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span(
            f"{request.method} {request.url.path}",
            kind=trace.SpanKind.SERVER,
        ) as span:
            # 添加请求属性
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.host", request.client.host if request.client else "unknown")
            
            # 添加租户和用户信息
            tenant_id = getattr(request.state, 'tenant_id', None)
            user_id = getattr(request.state, 'user_id', None)
            
            if tenant_id:
                span.set_attribute("tenant.id", tenant_id)
            if user_id:
                span.set_attribute("user.id", user_id)
            
            try:
                response = await call_next(request)
                span.set_attribute("http.status_code", response.status_code)
                return response
            except Exception as e:
                span.set_attribute("error", True)
                span.record_exception(e)
                raise

