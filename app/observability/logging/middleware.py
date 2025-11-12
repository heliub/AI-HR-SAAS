"""
Logging middleware
"""
import time
import uuid
import json
from typing import Dict, Any, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
import structlog

logger = structlog.get_logger()
class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件"""
    
    # 敏感字段，不记录到日志中
    SENSITIVE_HEADERS = {
        'authorization', 'cookie', 'x-api-key', 'x-csrf-token'
    }
    
    # 不记录body的Content-Type
    SKIP_BODY_CONTENT_TYPES = {
        'multipart/form-data',
        'application/octet-stream',
        'image/',
        'video/',
        'audio/',
        'application/pdf',
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
    
    def _should_skip_body(self, content_type: Optional[str]) -> bool:
        """判断是否应该跳过body记录"""
        if not content_type:
            return False
        content_type_lower = content_type.lower()
        return any(skip_type in content_type_lower for skip_type in self.SKIP_BODY_CONTENT_TYPES)
    
    async def _get_request_body(self, request: Request) -> Any:
        """安全地获取请求体（仅JSON）"""
        try:
            content_type = request.headers.get('content-type', '')
            
            # 跳过文件类型
            if self._should_skip_body(content_type):
                return "[BINARY/FILE CONTENT SKIPPED]"
            
            # 只处理JSON
            if 'application/json' not in content_type.lower():
                return None
            
            body = await request.body()
            if body:
                try:
                    return json.loads(body.decode('utf-8'))
                except json.JSONDecodeError:
                    return None
            return None
        except Exception:
            return None
    
    def _get_response_body(self, body: bytes, content_type: Optional[str]) -> Any:
        """安全地获取响应体（仅JSON）"""
        try:
            # 跳过文件类型
            if self._should_skip_body(content_type):
                return "[BINARY/FILE CONTENT SKIPPED]"
            
            # 只处理JSON
            if not content_type or 'application/json' not in content_type.lower():
                return None
            
            if body:
                try:
                    return json.loads(body.decode('utf-8'))
                except json.JSONDecodeError:
                    return None
            return None
        except Exception:
            return None
    
    async def dispatch(self, request: Request, call_next):      
        start_time = time.time()
        try:
            response: Response = await call_next(request)
            await self.log_request(request, start_time, response=response)
            return response
        except Exception as e:
            await self.log_request(request, start_time, exception=e)
            raise

    async def log_request(self, request: Request, start_time: float, response: Optional[Response] = None, exception: Optional[Exception] = None):
        duration = time.time() - start_time
        try:
            # 获取请求体
            request_body = await self._get_request_body(request)
            method = request.method
            path = request.url.path
            client_ip = request.client.host if request.client else None
            query_params = dict(request.query_params)
            headers = dict(request.headers)
            sanitized_headers = self._sanitize_headers(headers)
            
            if exception:
                logger.error(
                    "request_failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    duration_ms=f"{duration * 1000:.2f}ms",
                    query_params=query_params if query_params else None,
                    request_body=request_body,
                    exc_info=True,
                    method=method,
                    path=path,
                    client_ip=client_ip,
                )
            else:
                # 记录请求完成，包含完整信息
                logger.info(
                    "request_completed",
                    status_code=response.status_code,
                    duration_ms=f"{duration * 1000:.2f}ms",
                    query_params=query_params if query_params else None,
                    request_body=request_body,
                    headers=sanitized_headers,
                    method=method,
                    path=path,
                    client_ip=client_ip,
                )
        except Exception as e:
            logger.error("Failed to log request", error=str(e))
