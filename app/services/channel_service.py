"""
Channel service
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel import Channel
from app.services.base import BaseService
from app.core.exceptions import NotFoundException


class ChannelService(BaseService[Channel]):
    """渠道服务"""

    def __init__(self):
        super().__init__(Channel)

    async def get_channels(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        *,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        status: Optional[str] = None,
        is_admin: bool = False
    ) -> tuple[List[Channel], int]:
        """获取渠道列表"""
        query = select(Channel).where(Channel.tenant_id == tenant_id)
        
        # 默认过滤掉已删除的渠道
        if status != "deleted":
            query = query.where(Channel.status != "deleted")

        # 用户级数据隔离 - 只有非管理员才过滤user_id
        if user_id and not is_admin:
            query = query.where(Channel.user_id == user_id)

        # 搜索条件
        if search:
            query = query.where(
                or_(
                    Channel.name.ilike(f"%{search}%"),
                    Channel.description.ilike(f"%{search}%")
                )
            )

        # 状态筛选
        if status:
            query = query.where(Channel.status == status)

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)

        # 分页
        query = query.order_by(Channel.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        channels = result.scalars().all()

        return list(channels), total or 0

    async def create_channel(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        user_id: UUID,
        **channel_data
    ) -> Channel:
        """创建渠道"""
        channel_data.update({
            "tenant_id": tenant_id,
            "user_id": user_id
        })

        channel = Channel(**channel_data)
        db.add(channel)
        await db.commit()
        await db.refresh(channel)

        return channel

    async def update_channel(
        self,
        db: AsyncSession,
        channel_id: UUID,
        **update_data
    ) -> Channel:
        """更新渠道"""
        channel = await self.get(db, channel_id)
        if not channel:
            raise NotFoundException("Channel not found")

        for key, value in update_data.items():
            if value is not None:
                setattr(channel, key, value)

        await db.commit()
        await db.refresh(channel)

        return channel

    async def sync_channel(
        self,
        db: AsyncSession,
        channel_id: UUID
    ) -> dict:
        """同步渠道数据（模拟实现）"""
        channel = await self.get(db, channel_id)
        if not channel:
            raise NotFoundException("Channel not found")

        # 模拟同步结果
        from datetime import datetime

        # 更新最后同步时间
        channel.last_sync_at = datetime.utcnow()
        await db.commit()

        # 模拟返回新简历数量
        import random
        new_resumes = random.randint(1, 10)

        return {
            "newResumes": new_resumes,
            "syncedAt": channel.last_sync_at
        }

    async def delete_channel(
        self,
        db: AsyncSession,
        channel_id: UUID
    ) -> bool:
        """逻辑删除渠道（将状态设置为deleted）"""
        channel = await self.get(db, channel_id)
        if not channel:
            raise NotFoundException("Channel not found")
        
        # 逻辑删除：将状态设置为deleted
        channel.status = "deleted"
        await db.commit()
        
        return True
    
    async def hard_delete_channel(
        self,
        db: AsyncSession,
        channel_id: UUID
    ) -> bool:
        """物理删除渠道"""
        return await self.delete(db, channel_id)
    
    async def update_channel_status(
        self,
        db: AsyncSession,
        channel_id: UUID,
        status: str
    ) -> Channel:
        """更新渠道状态"""
        channel = await self.get(db, channel_id)
        if not channel:
            raise NotFoundException("Channel not found")
        
        # 验证状态值
        valid_statuses = ["active", "inactive", "deleted"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        channel.status = status
        await db.commit()
        await db.refresh(channel)
        
        return channel