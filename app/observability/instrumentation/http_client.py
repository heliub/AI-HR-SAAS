"""
HTTP客户端日志

提供带自动日志和trace传递的httpx客户端
"""
import time
from typing import Any
import httpx
import structlog

from app.observability import context

logger = structlog.get_logger(__name__)


class TracedAsyncClient(httpx.AsyncClient):
    """带日志和trace的httpx客户端"""
    
    # 敏感headers，需要脱敏
    SENSITIVE_HEADERS = {'authorization', 'x-api-key', 'cookie', 'x-auth-token'}
    
    def _sanitize_headers(self, headers: dict) -> dict:
        """清理敏感headers"""
        return {
            k: '***REDACTED***' if k.lower() in self.SENSITIVE_HEADERS else v
            for k, v in headers.items()
        }
    
    async def request(self, method: str, url: Any, **kwargs) -> httpx.Response:
        """
        发送HTTP请求（自动注入trace_id并记录日志）
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            httpx.Response: 响应对象
        """
        # 注入X-Trace-Id到请求header
        headers = kwargs.get('headers', {})
        if isinstance(headers, dict):
            trace_id = context.get_trace_id()
            if trace_id and 'X-Trace-Id' not in headers:
                headers['X-Trace-Id'] = trace_id
                kwargs['headers'] = headers
        
        start_time = time.time()
        
        try:
            response = await super().request(method, url, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            # 记录成功请求
            logger.info(
                "http_request",
                method=method,
                url=str(url),
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                request_headers=self._sanitize_headers(dict(response.request.headers))
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # 记录失败请求
            logger.error(
                "http_request_failed",
                method=method,
                url=str(url),
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=round(duration_ms, 2)
            )
            raise


# 提供同步版本（如果需要）
class TracedClient(httpx.Client):
    """带日志和trace的httpx同步客户端"""
    
    SENSITIVE_HEADERS = {'authorization', 'x-api-key', 'cookie', 'x-auth-token'}
    
    def _sanitize_headers(self, headers: dict) -> dict:
        """清理敏感headers"""
        return {
            k: '***REDACTED***' if k.lower() in self.SENSITIVE_HEADERS else v
            for k, v in headers.items()
        }
    
    def request(self, method: str, url: Any, **kwargs) -> httpx.Response:
        """
        发送HTTP请求（自动注入trace_id并记录日志）
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            httpx.Response: 响应对象
        """
        # 注入X-Trace-Id到请求header
        headers = kwargs.get('headers', {})
        if isinstance(headers, dict):
            trace_id = context.get_trace_id()
            if trace_id and 'X-Trace-Id' not in headers:
                headers['X-Trace-Id'] = trace_id
                kwargs['headers'] = headers
        
        start_time = time.time()
        
        try:
            response = super().request(method, url, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            # 记录成功请求
            logger.info(
                "http_request",
                method=method,
                url=str(url),
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                request_headers=self._sanitize_headers(dict(response.request.headers))
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # 记录失败请求
            logger.error(
                "http_request_failed",
                method=method,
                url=str(url),
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=round(duration_ms, 2)
            )
            raise

