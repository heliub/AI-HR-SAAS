"""
Metrics middleware
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.observability.metrics.setup import (
    http_requests_total,
    http_request_duration_seconds,
    active_requests,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """指标收集中间件"""
    
    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path
        
        # 增加活跃请求计数
        active_requests.labels(method=method, endpoint=path).inc()
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            status_code = response.status_code
            
            # 记录指标
            http_requests_total.labels(
                method=method,
                endpoint=path,
                status=status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=path
            ).observe(duration)
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            http_requests_total.labels(
                method=method,
                endpoint=path,
                status=500
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=path
            ).observe(duration)
            
            raise
        finally:
            # 减少活跃请求计数
            active_requests.labels(method=method, endpoint=path).dec()

