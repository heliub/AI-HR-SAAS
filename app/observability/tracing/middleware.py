"""
Tracing middleware - 轻量级实现
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.observability import context
from app.observability.tracing.trace import trace_span


class TraceMiddleware(BaseHTTPMiddleware):
    """Trace中间件 - 处理X-Trace-Id的接收和传递"""
    
    async def dispatch(self, request: Request, call_next):
        # 从header获取trace_id，如果没有则生成新的
        trace_id = request.headers.get('X-Trace-Id')
        if trace_id:
            context.set_trace_id(trace_id)
        else:
            trace_id = context.new_trace_id()
        try:
            # 创建请求级span（不记录span日志，避免冗余）
            with trace_span(f"{request.method} {request.url.path}", log_span=False):
                response = await call_next(request)
            # 在响应header中返回trace_id
            response.headers['X-Trace-Id'] = trace_id
            return response
        finally:
            # 清理上下文，防止协程复用导致traceId冲突
            context.clear_context()

