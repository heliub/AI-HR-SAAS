"""
Base service class
"""
from typing import Generic, TypeVar, Type, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base
from app.infrastructure.database.repository import BaseRepository

ModelType = TypeVar("ModelType", bound=Base)


class BaseService(Generic[ModelType]):
    """基础服务类"""
    
    def __init__(self, model: Type[ModelType]):
        self.repository = BaseRepository(model)
    
    async def get_by_id(
        self, 
        db: AsyncSession, 
        id: int, 
        tenant_id: Optional[int] = None
    ) -> Optional[ModelType]:
        """根据ID获取"""
        return await self.repository.get_by_id(db, id, tenant_id)
    
    async def get(
        self, 
        db: AsyncSession, 
        id: int, 
        tenant_id: Optional[int] = None
    ) -> Optional[ModelType]:
        """根据ID获取（get_by_id的别名）"""
        return await self.get_by_id(db, id, tenant_id)
    
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        tenant_id: Optional[int] = None,
    ):
        """获取多条记录"""
        return await self.repository.get_multi(
            db,
            skip=skip,
            limit=limit,
            tenant_id=tenant_id
        )
    
    async def delete(
        self,
        db: AsyncSession,
        id: int,
        tenant_id: Optional[int] = None
    ) -> bool:
        """删除记录"""
        return await self.repository.delete(
            db,
            id=id,
            tenant_id=tenant_id
        )

