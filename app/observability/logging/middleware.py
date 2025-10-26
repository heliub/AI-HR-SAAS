"""
Logging middleware
"""
import time
import uuid
import json
from typing import Dict, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件"""
    
    # 敏感字段，不记录到日志中
    SENSITIVE_HEADERS = {
        'authorization', 'cookie', 'x-api-key', 'x-csrf-token'
    }
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """清理敏感的header信息"""
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.SENSITIVE_HEADERS:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized
    
    async def _get_request_body(self, request: Request) -> Any:
        """安全地获取请求体"""
        try:
            # 先尝试获取JSON
            body = await request.body()
            if body:
                try:
                    return json.loads(body.decode('utf-8'))
                except json.JSONDecodeError:
                    # 如果不是JSON，返回前100个字符
                    body_str = body.decode('utf-8', errors='ignore')
                    return body_str[:100] + "..." if len(body_str) > 100 else body_str
            return None
        except Exception:
            return None
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 获取请求信息
        query_params = dict(request.query_params)
        headers = dict(request.headers)
        sanitized_headers = self._sanitize_headers(headers)
        
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
        
        # 记录请求开始，包含完整信息
        logger.info(
            "request_started",
            query_params=query_params if query_params else None,
            headers=sanitized_headers,
            user_agent=headers.get('user-agent'),
        )
        
        try:
            response: Response = await call_next(request)
            duration = time.time() - start_time
            
            # 记录请求完成，包含完整信息
            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration=f"{duration:.3f}s",
                duration_ms=f"{duration * 1000:.2f}ms",
                query_params=query_params if query_params else None,
                response_headers=dict(response.headers),
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
                duration_ms=f"{duration * 1000:.2f}ms",
                query_params=query_params if query_params else None,
                exc_info=True
            )
            raise

