"""
User service
"""
from typing import Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.base import BaseService
from app.core.security import security_manager
from app.core.exceptions import NotFoundException, BadRequestException


class UserService(BaseService[User]):
    """用户服务"""
    
    def __init__(self):
        super().__init__(User)
    
    async def get_by_email(
        self,
        db: AsyncSession,
        email: str,
        tenant_id: int
    ) -> Optional[User]:
        """根据邮箱获取用户"""
        query = select(User).where(
            User.email == email,
            User.tenant_id == tenant_id,
            User.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_user(
        self,
        db: AsyncSession,
        *,
        tenant_id: int,
        username: str,
        email: str,
        password: str,
        **kwargs
    ) -> User:
        """创建用户"""
        # 检查邮箱是否已存在
        existing_user = await self.get_by_email(db, email, tenant_id)
        if existing_user:
            raise BadRequestException("Email already registered")
        
        # 创建用户
        hashed_password = security_manager.hash_password(password)
        
        user_data = {
            "tenant_id": tenant_id,
            "username": username,
            "email": email,
            "password_hash": hashed_password,
            **kwargs
        }
        
        user = await self.repository.create(db, user_data)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    async def authenticate(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        tenant_id: int
    ) -> Optional[User]:
        """认证用户"""
        user = await self.get_by_email(db, email, tenant_id)
        
        if not user:
            return None
        
        if not security_manager.verify_password(password, user.password_hash):
            return None
        
        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        await db.commit()
        
        return user

