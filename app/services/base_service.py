"""
Base service class for database operations
"""
from typing import Any, Dict, List, Optional, Type
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, func

from app.models.base import Base


class BaseService:
    """基础服务类，提供通用的数据库操作方法"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, model: Type[Base], record_id: UUID, tenant_id: Optional[UUID] = None) -> Optional[Base]:
        """根据ID获取记录"""
        conditions = [model.id == record_id]
        if tenant_id and hasattr(model, 'tenant_id'):
            conditions.append(model.tenant_id == tenant_id)

        query = select(model).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalar()

    async def get_all(
        self,
        model: Type[Base],
        tenant_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        is_admin: bool = False
    ) -> List[Base]:
        """获取所有记录"""
        conditions = []

        # 租户过滤
        if tenant_id and hasattr(model, 'tenant_id'):
            conditions.append(model.tenant_id == tenant_id)

        # 用户过滤 - 只有非管理员且模型有user_id字段时才过滤
        if user_id and not is_admin and hasattr(model, 'user_id'):
            conditions.append(model.user_id == user_id)

        # 自定义过滤
        if filters:
            for key, value in filters.items():
                if hasattr(model, key):
                    conditions.append(getattr(model, key) == value)

        query = select(model).where(and_(*conditions)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, model: Type[Base], data: Dict[str, Any]) -> Base:
        """创建新记录"""
        db_obj = model(**data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, model: Type[Base], record_id: UUID, data: Dict[str, Any], tenant_id: Optional[UUID] = None) -> Optional[Base]:
        """更新记录"""
        db_obj = await self.get_by_id(model, record_id, tenant_id)
        if db_obj:
            for key, value in data.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            await self.db.commit()
            await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, model: Type[Base], record_id: UUID, tenant_id: Optional[UUID] = None) -> bool:
        """删除记录"""
        db_obj = await self.get_by_id(model, record_id, tenant_id)
        if db_obj:
            self.db.delete(db_obj)
            await self.db.commit()
            return True
        return False

    async def count(self, model: Type[Base], tenant_id: Optional[UUID] = None, user_id: Optional[UUID] = None, filters: Optional[Dict[str, Any]] = None, is_admin: bool = False) -> int:
        """统计记录数量"""
        conditions = []

        if tenant_id and hasattr(model, 'tenant_id'):
            conditions.append(model.tenant_id == tenant_id)

        # 用户过滤 - 只有非管理员且模型有user_id字段时才过滤
        if user_id and not is_admin and hasattr(model, 'user_id'):
            conditions.append(model.user_id == user_id)

        if filters:
            for key, value in filters.items():
                if hasattr(model, key):
                    conditions.append(getattr(model, key) == value)

        query = select(func.count(model.id)).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalar()

    async def count_without_tenant_filter(self, model: Type[Base], user_id: Optional[UUID] = None, filters: Optional[Dict[str, Any]] = None, is_admin: bool = False) -> int:
        """统计记录数量（不限制tenant，用于管理员）"""
        conditions = []

        # 用户过滤 - 只有非管理员且模型有user_id字段时才过滤
        if user_id and not is_admin and hasattr(model, 'user_id'):
            conditions.append(model.user_id == user_id)

        if filters:
            for key, value in filters.items():
                if hasattr(model, key):
                    conditions.append(getattr(model, key) == value)

        query = select(func.count(model.id)).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalar()