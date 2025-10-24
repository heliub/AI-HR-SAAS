"""
FastAPI dependencies
"""
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import security, security_manager
from app.infrastructure.database.session import get_db
from app.infrastructure.cache.redis import get_redis
from app.models.user import User
from app.services.user_service import UserService


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    获取当前认证用户
    
    Args:
        credentials: HTTP Bearer凭证
        db: 数据库会话
    
    Returns:
        当前用户对象
    
    Raises:
        HTTPException: 认证失败
    """
    token = credentials.credentials
    
    # 验证Token
    payload = security_manager.verify_token(token)
    
    user_id: Optional[int] = payload.get("sub")
    tenant_id: Optional[int] = payload.get("tenant_id")
    
    if user_id is None or tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 获取用户
    user_service = UserService()
    user = await user_service.get_by_id(db, user_id, tenant_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active",
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户"""
    if current_user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前管理员用户"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

