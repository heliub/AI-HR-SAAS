"""
Auth Token service for token management
"""
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.auth_token import AuthToken
from app.core.security import security_manager


class AuthTokenService:
    """认证Token服务"""

    async def create_token(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: str,
        token: str,
        expires_at: datetime
    ) -> AuthToken:
        """
        创建token记录

        Args:
            db: 数据库会话
            tenant_id: 租户ID
            user_id: 用户ID
            token: JWT Token字符串
            expires_at: 过期时间

        Returns:
            AuthToken对象
        """
        auth_token = AuthToken(
            tenant_id=tenant_id,
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            is_revoked=False
        )

        db.add(auth_token)
        await db.commit()
        await db.refresh(auth_token)

        return auth_token

    async def revoke_token(
        self,
        db: AsyncSession,
        token: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        撤销token（加入黑名单）

        Args:
            db: 数据库会话
            token: JWT Token字符串
            user_id: 用户ID（可选，用于额外验证）

        Returns:
            是否成功撤销
        """
        query = select(AuthToken).where(AuthToken.token == token)

        if user_id:
            query = query.where(AuthToken.user_id == user_id)

        result = await db.execute(query)
        auth_token = result.scalar_one_or_none()

        if not auth_token:
            return False

        auth_token.is_revoked = True
        auth_token.updated_at = datetime.now(timezone.utc)

        await db.commit()
        return True

    async def revoke_all_user_tokens(
        self,
        db: AsyncSession,
        user_id: str
    ) -> int:
        """
        撤销用户的所有token（强制登出所有设备）

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            撤销的token数量
        """
        query = select(AuthToken).where(
            and_(
                AuthToken.user_id == user_id,
                AuthToken.is_revoked == False,
                AuthToken.expires_at > datetime.now(timezone.utc)
            )
        )

        result = await db.execute(query)
        tokens = result.scalars().all()

        count = 0
        for token in tokens:
            token.is_revoked = True
            token.updated_at = datetime.now(timezone.utc)
            count += 1

        await db.commit()
        return count

    async def is_token_revoked(
        self,
        db: AsyncSession,
        token: str
    ) -> bool:
        """
        检查token是否已被撤销

        Args:
            db: 数据库会话
            token: JWT Token字符串

        Returns:
            是否已被撤销
        """
        query = select(AuthToken).where(
            and_(
                AuthToken.token == token,
                AuthToken.is_revoked == True
            )
        )

        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    async def is_token_valid(
        self,
        db: AsyncSession,
        token: str
    ) -> bool:
        """
        检查token是否有效（未撤销且未过期）

        Args:
            db: 数据库会话
            token: JWT Token字符串

        Returns:
            是否有效
        """
        # 先检查JWT本身是否有效
        try:
            security_manager.verify_token(token)
        except Exception:
            return False

        # 检查token是否在黑名单中
        if await self.is_token_revoked(db, token):
            return False

        # 检查token是否在数据库中存在且未过期
        query = select(AuthToken).where(
            and_(
                AuthToken.token == token,
                AuthToken.is_revoked == False,
                AuthToken.expires_at > datetime.now(timezone.utc)
            )
        )

        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    async def cleanup_expired_tokens(
        self,
        db: AsyncSession,
        tenant_id: Optional[str] = None
    ) -> int:
        """
        清理过期的token记录

        Args:
            db: 数据库会话
            tenant_id: 租户ID（可选，用于清理特定租户的过期token）

        Returns:
            清理的token数量
        """
        query = select(AuthToken).where(AuthToken.expires_at < datetime.now(timezone.utc))

        if tenant_id:
            query = query.where(AuthToken.tenant_id == tenant_id)

        result = await db.execute(query)
        expired_tokens = result.scalars().all()

        count = 0
        for token in expired_tokens:
            await db.delete(token)
            count += 1

        await db.commit()
        return count

    async def get_user_active_tokens(
        self,
        db: AsyncSession,
        user_id: str
    ) -> List[AuthToken]:
        """
        获取用户的所有有效token

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            有效token列表
        """
        query = select(AuthToken).where(
            and_(
                AuthToken.user_id == user_id,
                AuthToken.is_revoked == False,
                AuthToken.expires_at > datetime.now(timezone.utc)
            )
        ).order_by(AuthToken.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()