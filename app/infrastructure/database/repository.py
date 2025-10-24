"""
Base repository pattern
"""
from typing import Generic, TypeVar, Type, Optional, List, Any, Dict

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """基础仓储类"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def get_by_id(
        self, 
        db: AsyncSession, 
        id: int, 
        tenant_id: Optional[int] = None
    ) -> Optional[ModelType]:
        """根据ID获取记录"""
        query = select(self.model).where(self.model.id == id)
        
        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        tenant_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """获取多条记录"""
        query = select(self.model)
        
        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def create(
        self, 
        db: AsyncSession, 
        obj_in: Dict[str, Any]
    ) -> ModelType:
        """创建记录"""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self,
        db: AsyncSession,
        *,
        id: int,
        obj_in: Dict[str, Any],
        tenant_id: Optional[int] = None,
    ) -> Optional[ModelType]:
        """更新记录"""
        query = update(self.model).where(self.model.id == id)
        
        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)
        
        query = query.values(**obj_in).returning(self.model)
        
        result = await db.execute(query)
        await db.commit()
        
        return result.scalar_one_or_none()
    
    async def delete(
        self,
        db: AsyncSession,
        *,
        id: int,
        tenant_id: Optional[int] = None,
    ) -> bool:
        """删除记录"""
        query = delete(self.model).where(self.model.id == id)
        
        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)
        
        result = await db.execute(query)
        await db.commit()
        
        return result.rowcount > 0
    
    async def count(
        self,
        db: AsyncSession,
        *,
        tenant_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """统计记录数"""
        query = select(func.count()).select_from(self.model)
        
        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        result = await db.execute(query)
        return result.scalar_one()

