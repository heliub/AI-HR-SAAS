"""
API安全中间件
包含限流、防护、日志等功能
"""
import time
import asyncio
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict, deque
from datetime import datetime, timedelta
import hashlib
import ipaddress
from uuid import uuid4

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog

logger = structlog.get_logger(__name__)


class RateLimiter:
    """基于内存的限流器"""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)

    def is_allowed(self, key: str) -> bool:
        """检查是否允许请求"""
        now = time.time()
        request_times = self.requests[key]

        # 清理过期的请求记录
        while request_times and request_times[0] <= now - self.window_seconds:
            request_times.popleft()

        # 检查是否超过限制
        if len(request_times) >= self.max_requests:
            return False

        # 记录当前请求
        request_times.append(now)
        return True


class RedisRateLimiter:
    """基于Redis的分布式限流器"""

    def __init__(self, redis_client, max_requests: int, window_seconds: int):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def is_allowed(self, key: str) -> bool:
        """检查是否允许请求"""
        try:
            current_time = int(time.time())
            window_start = current_time - self.window_seconds

            # 使用滑动窗口算法
            pipeline = self.redis.pipeline()
            pipeline.zremrangebyscore(key, 0, window_start)
            pipeline.zcard(key)
            pipeline.zadd(key, {str(current_time): current_time})
            pipeline.expire(key, self.window_seconds)

            results = await pipeline.execute()
            current_count = results[1]

            return current_count < self.max_requests
        except Exception as e:
            logger.error("Redis rate limiter error", error=str(e), key=key)
            # 如果Redis出错，允许请求通过（避免影响业务）
            return True


class SecurityConfig:
    """安全配置"""

    # 限流配置
    RATE_LIMITS = {
        "default": {"max_requests": 100, "window_seconds": 60},
        "auth": {"max_requests": 10, "window_seconds": 60},
        "upload": {"max_requests": 20, "window_seconds": 60},
        "export": {"max_requests": 5, "window_seconds": 300},
        "search": {"max_requests": 50, "window_seconds": 60},
    }

    # IP白名单
    ALLOWED_IPS = [
        "127.0.0.1",  # 本地
        "::1",         # IPv6本地
    ]

    # 可信代理（用于获取真实IP）
    TRUSTED_PROXIES = [
        "127.0.0.1",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
    ]

    # 安全头部
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件"""

    def __init__(
        self,
        app: ASGIApp,
        redis_client=None,
        enable_rate_limiting: bool = True,
        enable_ip_filtering: bool = True,
        enable_security_headers: bool = True,
    ):
        super().__init__(app)
        self.redis_client = redis_client
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_ip_filtering = enable_ip_filtering
        self.enable_security_headers = enable_security_headers

        # 初始化限流器
        self.rate_limiters: Dict[str, Any] = {}
        for key, config in SecurityConfig.RATE_LIMITS.items():
            if redis_client:
                self.rate_limiters[key] = RedisRateLimiter(
                    redis_client, config["max_requests"], config["window_seconds"]
                )
            else:
                self.rate_limiters[key] = RateLimiter(
                    config["max_requests"], config["window_seconds"]
                )

        # IP阻止列表（动态）
        self.blocked_ips: Dict[str, datetime] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        start_time = time.time()
        client_ip = self.get_client_ip(request)

        try:
            # 1. IP过滤
            if self.enable_ip_filtering:
                if not await self.check_ip_allowed(client_ip):
                    return self.create_security_response(
                        "IP blocked", status.HTTP_403_FORBIDDEN
                    )

            # 2. 限流检查
            if self.enable_rate_limiting:
                if not await self.check_rate_limit(request, client_ip):
                    return self.create_security_response(
                        "Rate limit exceeded", status.HTTP_429_TOO_MANY_REQUESTS,
                        headers={"Retry-After": "60"}
                    )

            # 3. 处理请求
            response = await call_next(request)

            # 4. 添加安全头部
            if self.enable_security_headers:
                self.add_security_headers(response)

            # 5. 记录请求日志
            await self.log_request(request, response, client_ip, start_time)

            return response

        except Exception as e:
            logger.error("Security middleware error", error=str(e), ip=client_ip)
            return self.create_security_response(
                "Internal security error", status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_client_ip(self, request: Request) -> str:
        """获取真实客户端IP"""
        # 检查代理头部
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ips = forwarded_for.split(",")
            for ip in reversed(ips):  # 最右边的IP是最原始的客户端IP
                ip = ip.strip()
                if self.is_trusted_proxy(ip):
                    continue
                return ip

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        return request.client.host if request.client else "unknown"

    def is_trusted_proxy(self, ip: str) -> bool:
        """检查IP是否为可信代理"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            for trusted_range in SecurityConfig.TRUSTED_PROXIES:
                if "/" in trusted_range:
                    network = ipaddress.ip_network(trusted_range)
                    if ip_obj in network:
                        return True
                else:
                    if ip_obj == ipaddress.ip_address(trusted_range):
                        return True
        except ValueError:
            pass
        return False

    async def check_ip_allowed(self, ip: str) -> bool:
        """检查IP是否被允许"""
        try:
            # 检查IP是否在阻止列表中
            if ip in self.blocked_ips:
                block_time = self.blocked_ips[ip]
                if datetime.utcnow() < block_time:
                    return False
                else:
                    # 阻止时间已过，移除阻止
                    del self.blocked_ips[ip]

            # 检查IP是否在白名单中
            if SecurityConfig.ALLOWED_IPS:
                try:
                    ip_obj = ipaddress.ip_address(ip)
                    for allowed in SecurityConfig.ALLOWED_IPS:
                        if ip_obj == ipaddress.ip_address(allowed):
                            return True
                except ValueError:
                    pass

                # 如果有白名单但IP不在其中，阻止访问
                return False

            return True

        except Exception as e:
            logger.error("IP filtering error", error=str(e), ip=ip)
            return True  # 出错时允许访问

    async def check_rate_limit(self, request: Request, ip: str) -> bool:
        """检查限流"""
        try:
            # 根据请求路径确定限流策略
            path = request.url.path
            rate_limit_key = self.get_rate_limit_key(path)

            if rate_limit_key not in self.rate_limiters:
                return True

            limiter = self.rate_limiters[rate_limit_key]

            # 构建限流键（IP + 用户ID + 路径）
            user_id = getattr(request.state, "user_id", None)
            limit_key = f"{rate_limit_key}:{ip}"
            if user_id:
                limit_key += f":{user_id}"

            return await limiter.is_allowed(limit_key)

        except Exception as e:
            logger.error("Rate limiting error", error=str(e), ip=ip)
            return True  # 出错时允许访问

    def get_rate_limit_key(self, path: str) -> str:
        """根据路径确定限流策略"""
        if "/auth" in path:
            return "auth"
        elif "/upload" in path:
            return "upload"
        elif "/export" in path:
            return "export"
        elif "/search" in path:
            return "search"
        else:
            return "default"

    def add_security_headers(self, response: Response):
        """添加安全头部"""
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value

    async def log_request(
        self, request: Request, response: Response, ip: str, start_time: float
    ):
        """记录请求日志"""
        try:
            duration = time.time() - start_time
            user_id = getattr(request.state, "user_id", None)
            tenant_id = getattr(request.state, "tenant_id", None)

            log_data = {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": duration,
                "ip": ip,
                "user_agent": request.headers.get("User-Agent", ""),
                "user_id": str(user_id) if user_id else None,
                "tenant_id": str(tenant_id) if tenant_id else None,
            }

            # 记录慢请求
            if duration > 1.0:
                logger.warning("Slow request detected", **log_data)
            else:
                logger.info("Request completed", **log_data)

            # 记录错误请求
            if response.status_code >= 400:
                logger.warning("HTTP error response", **log_data)

        except Exception as e:
            logger.error("Request logging error", error=str(e))

    def create_security_response(
        self, message: str, status_code: int, headers: Optional[Dict] = None
    ) -> JSONResponse:
        """创建安全响应"""
        response_data = {
            "error": message,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid4()),
        }

        response = JSONResponse(
            content=response_data,
            status_code=status_code,
            headers=headers or {},
        )
        return response

    async def block_ip(self, ip: str, duration_minutes: int = 60):
        """阻止IP"""
        block_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.blocked_ips[ip] = block_until
        logger.warning("IP blocked", ip=ip, duration_minutes=duration_minutes)


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """请求大小限制中间件"""

    def __init__(self, app: ASGIApp, max_size_mb: int = 10):
        super().__init__(app)
        self.max_size = max_size_mb * 1024 * 1024  # 转换为字节

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """检查请求大小"""
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error": "Request too large",
                    "max_size_mb": self.max_size // (1024 * 1024),
                },
            )

        return await call_next(request)


class CORSMiddleware(BaseHTTPMiddleware):
    """CORS中间件"""

    def __init__(
        self,
        app: ASGIApp,
        allow_origins: List[str] = None,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        allow_credentials: bool = False,
    ):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理CORS"""
        origin = request.headers.get("origin")

        if origin and (self.allow_origins == ["*"] or origin in self.allow_origins):
            response = await call_next(request)
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)

            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"

            if request.method == "OPTIONS":
                response.headers["Access-Control-Max-Age"] = "86400"
                return response

            return response

        return await call_next(request)


# 安全中间件工厂函数
def create_security_middleware(
    app: ASGIApp,
    redis_client=None,
    security_config: Optional[Dict] = None,
) -> List[BaseHTTPMiddleware]:
    """
    创建安全中间件堆栈

    Args:
        app: ASGI应用
        redis_client: Redis客户端
        security_config: 安全配置

    Returns:
        中间件列表
    """
    middlewares = []

    # 1. CORS中间件（最外层）
    middlewares.append(CORSMiddleware(app))

    # 2. 请求大小限制
    max_size = (security_config or {}).get("max_request_size_mb", 10)
    middlewares.append(RequestSizeMiddleware(app, max_size))

    # 3. 安全中间件
    middlewares.append(
        SecurityMiddleware(
            app,
            redis_client=redis_client,
            enable_rate_limiting=(security_config or {}).get("enable_rate_limiting", True),
            enable_ip_filtering=(security_config or {}).get("enable_ip_filtering", True),
            enable_security_headers=(security_config or {}).get("enable_security_headers", True),
        )
    )

    return middlewares