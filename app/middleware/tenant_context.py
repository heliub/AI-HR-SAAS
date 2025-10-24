"""
Tenant context middleware
"""
from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# 租户和用户上下文变量
tenant_context: ContextVar[Optional[int]] = ContextVar('tenant_context', default=None)
user_context: ContextVar[Optional[int]] = ContextVar('user_context', default=None)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """租户上下文中间件"""
    
    async def dispatch(self, request: Request, call_next):
        # 从request.state获取租户和用户信息（由认证依赖注入设置）
        tenant_id = getattr(request.state, 'tenant_id', None)
        user_id = getattr(request.state, 'user_id', None)
        
        # 设置上下文
        token_tenant = tenant_context.set(tenant_id)
        token_user = user_context.set(user_id)
        
        try:
            response = await call_next(request)
            return response
        finally:
            # 重置上下文
            tenant_context.reset(token_tenant)
            user_context.reset(token_user)


def get_current_tenant_id() -> Optional[int]:
    """获取当前租户ID"""
    return tenant_context.get()


def get_current_user_id() -> Optional[int]:
    """获取当前用户ID"""
    return user_context.get()

