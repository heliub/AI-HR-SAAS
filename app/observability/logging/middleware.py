"""
Logging middleware
"""
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 绑定请求上下文
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None,
        )
        
        # 从request.state获取租户和用户信息（由认证中间件设置）
        tenant_id = getattr(request.state, 'tenant_id', None)
        user_id = getattr(request.state, 'user_id', None)
        
        if tenant_id:
            structlog.contextvars.bind_contextvars(tenant_id=tenant_id)
        if user_id:
            structlog.contextvars.bind_contextvars(user_id=user_id)
        
        logger = structlog.get_logger()
        
        start_time = time.time()
        logger.info("request_started")
        
        try:
            response: Response = await call_next(request)
            duration = time.time() - start_time
            
            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration=f"{duration:.3f}s"
            )
            
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "request_failed",
                error=str(e),
                error_type=type(e).__name__,
                duration=f"{duration:.3f}s",
                exc_info=True
            )
            raise

