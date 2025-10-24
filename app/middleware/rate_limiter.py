"""
Rate limiter middleware
"""
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException, status

from app.infrastructure.cache.redis import get_redis


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        """
        初始化速率限制器
        
        Args:
            app: FastAPI应用
            calls: 时间窗口内允许的调用次数
            period: 时间窗口（秒）
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
    
    async def dispatch(self, request: Request, call_next):
        # 跳过某些路径
        if request.url.path in ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # 获取客户端标识（IP或用户ID）
        client_id = self._get_client_id(request)
        
        # 检查速率限制
        if not await self._check_rate_limit(client_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        # 优先使用用户ID
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # 否则使用IP地址
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(self, client_id: str) -> bool:
        """检查速率限制"""
        try:
            redis = get_redis()
            key = f"rate_limit:{client_id}"
            
            # 获取当前计数
            current = await redis.get(key)
            
            if current is None:
                # 第一次请求，设置计数和过期时间
                await redis.setex(key, self.period, 1)
                return True
            
            current = int(current)
            
            if current >= self.calls:
                # 超过限制
                return False
            
            # 增加计数
            await redis.incr(key)
            return True
            
        except Exception:
            # Redis错误时允许请求通过
            return True

