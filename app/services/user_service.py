"""
User service
"""
from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.base import BaseService
from app.core.security import security_manager
from app.core.exceptions import NotFoundException, BadRequestException
from app.infrastructure.database.session import get_db_context


class UserService(BaseService[User]):
    """用户服务"""
    
    def __init__(self):
        super().__init__(User)
    
    async def get_by_email(
        self,
        db: AsyncSession,
        email: str,
        tenant_id: UUID
    ) -> Optional[User]:
        """根据邮箱获取用户"""
        query = select(User).where(
            User.email == email,
            User.tenant_id == tenant_id,
            User.is_active == True
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_email_any_tenant(
        self,
        db: AsyncSession,
        email: str
    ) -> Optional[User]:
        """根据邮箱获取用户（不限制租户）"""
        query = select(User).where(
            User.email == email,
            User.is_active == True
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_user(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        name: str,
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
            "name": name,
            "email": email,
            "password_hash": hashed_password,
            **kwargs
        }
        
        user = User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    async def authenticate(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        tenant_id: UUID
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
    
    async def update_password(
        self,
        db: AsyncSession,
        user_id: UUID,
        current_password: str,
        new_password: str
    ) -> bool:
        """更新密码"""
        user = await self.get(db, user_id)
        if not user:
            raise NotFoundException("User not found")

        # 验证当前密码
        if not security_manager.verify_password(current_password, user.password_hash):
            raise BadRequestException("Current password is incorrect")

        # 更新密码
        user.password_hash = security_manager.hash_password(new_password)
        await db.commit()

        return True

    async def update_profile(
        self,
        db: AsyncSession,
        user_id: UUID,
        name: Optional[str] = None,
        email: Optional[str] = None
    ) -> User:
        """更新个人信息（不允许修改角色）"""
        user = await self.get(db, user_id)
        if not user:
            raise NotFoundException("User not found")

        # 更新姓名
        if name is not None:
            user.name = name

        # 更新邮箱（需要检查唯一性）
        if email is not None and email != user.email:
            existing_user = await self.get_by_email(db, email, user.tenant_id)
            if existing_user and existing_user.id != user_id:
                raise BadRequestException("Email already registered")
            user.email = email

        await db.commit()
        await db.refresh(user)

        return user

    async def update_avatar(
        self,
        db: AsyncSession,
        user_id: UUID,
        avatar_url: str
    ) -> User:
        """更新头像"""
        user = await self.get(db, user_id)
        if not user:
            raise NotFoundException("User not found")

        user.avatar_url = avatar_url
        await db.commit()
        await db.refresh(user)

        return user

    async def update_user_settings(
        self,
        db: AsyncSession,
        user_id: UUID,
        language: Optional[str] = None,
        email_notifications: Optional[bool] = None,
        task_reminders: Optional[bool] = None
    ):
        """更新用户设置"""
        from app.models.user_setting import UserSetting
        from sqlalchemy import select

        user = await self.get(db, user_id)
        if not user:
            raise NotFoundException("User not found")

        # 查找或创建用户设置
        query = select(UserSetting).where(UserSetting.user_id == user_id)
        result = await db.execute(query)
        user_setting = result.scalar_one_or_none()

        if not user_setting:
            # 创建新的用户设置
            user_setting = UserSetting(
                tenant_id=user.tenant_id,
                user_id=user_id,
                language=language or 'zh',
                email_notifications=email_notifications if email_notifications is not None else True,
                task_reminders=task_reminders if task_reminders is not None else True
            )
            db.add(user_setting)
        else:
            # 更新现有设置
            if language is not None:
                user_setting.language = language
            if email_notifications is not None:
                user_setting.email_notifications = email_notifications
            if task_reminders is not None:
                user_setting.task_reminders = task_reminders

        await db.commit()
        await db.refresh(user_setting)

        return {
            "language": user_setting.language,
            "emailNotifications": user_setting.email_notifications,
            "taskReminders": user_setting.task_reminders
        }

    async def get_user_settings(
        self,
        user_id: UUID
    ):
        """获取用户设置"""
        from app.models.user_setting import UserSetting
        from sqlalchemy import select

        # 查找用户设置
        query = select(UserSetting).where(UserSetting.user_id == user_id)
        async with get_db_context() as session:
            result = await session.execute(query)
            user_setting = result.scalar_one_or_none()
            if not user_setting:
                # 返回默认设置
                return {
                    "language": None,
                    "emailNotifications": False,
                    "taskReminders": False
                }

            return {
                "language": user_setting.language,
                "emailNotifications": user_setting.email_notifications,
                "taskReminders": user_setting.task_reminders
            }

