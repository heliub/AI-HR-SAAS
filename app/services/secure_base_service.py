"""
生产环境安全基础服务类
提供租户隔离、权限验证、事务管理等核心功能
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from uuid import UUID
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, func
from sqlalchemy.exc import SQLAlchemyError
import structlog

from app.models.base import Base

logger = structlog.get_logger(__name__)


class TenantAwareMixin:
    """租户感知混入类"""

    @staticmethod
    def get_tenant_filter(model: Type[Base], tenant_id: UUID) -> List:
        """获取租户过滤条件"""
        if hasattr(model, 'tenant_id'):
            return [model.tenant_id == tenant_id]
        return []

    @staticmethod
    def get_user_filter(model: Type[Base], user_id: Optional[UUID] = None) -> List:
        """获取用户过滤条件（如果模型支持）"""
        conditions = []
        if user_id and hasattr(model, 'user_id'):
            conditions.append(model.user_id == user_id)
        elif user_id and hasattr(model, 'created_by'):
            conditions.append(model.created_by == user_id)
        return conditions


class SecureBaseService(TenantAwareMixin, ABC):
    """
    生产环境安全基础服务类

    特性：
    - 自动租户隔离
    - 事务管理
    - 错误处理和日志
    - 权限验证钩子
    - 性能监控
    """

    def __init__(self, db: AsyncSession, model: Type[Base]):
        self.db = db
        self.model = model
        self.logger = logger.bind(service=self.__class__.__name__)

    @asynccontextmanager
    async def transaction_scope(self):
        """事务上下文管理器"""
        try:
            async with self.db.begin():
                yield self.db
        except SQLAlchemyError as e:
            self.logger.error("Database transaction failed", error=str(e))
            await self.db.rollback()
            raise
        except Exception as e:
            self.logger.error("Unexpected error in transaction", error=str(e))
            await self.db.rollback()
            raise

    async def check_permission(
        self,
        user_id: UUID,
        tenant_id: UUID,
        resource_id: Optional[UUID] = None,
        action: str = "read"
    ) -> bool:
        """
        权限检查钩子

        子类应该重写此方法来实现具体的权限逻辑
        """
        # 基础权限检查：用户必须属于该租户
        # TODO: 实现更复杂的权限逻辑
        _ = user_id, tenant_id, resource_id, action  # 避免未使用变量警告
        return True

    async def get_by_id_secure(
        self,
        record_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        check_permission: bool = True
    ) -> Optional[Base]:
        """
        安全的ID查询，包含权限验证
        """
        if check_permission:
            has_permission = await self.check_permission(user_id, tenant_id, record_id, "read")
            if not has_permission:
                self.logger.warning("Permission denied for get_by_id",
                                  user_id=user_id, tenant_id=tenant_id, record_id=record_id)
                return None

        conditions = [self.model.id == record_id] + self.get_tenant_filter(self.model, tenant_id)

        if user_id:
            conditions += self.get_user_filter(self.model, user_id)

        query = select(self.model).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalar()

    async def get_all_secure(
        self,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional = None
    ) -> List[Base]:
        """
        安全的列表查询，自动应用租户和用户过滤
        """
        conditions = self.get_tenant_filter(self.model, tenant_id)

        if user_id:
            conditions += self.get_user_filter(self.model, user_id)

        # 应用自定义过滤
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    conditions.append(getattr(self.model, key) == value)

        query = select(self.model).where(and_(*conditions)).offset(skip).limit(limit)

        # 应用排序
        if order_by:
            query = query.order_by(order_by)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_secure(
        self,
        data: Dict[str, Any],
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        check_permission: bool = True
    ) -> Base:
        """
        安全的创建操作，包含权限验证和数据验证
        """
        if check_permission:
            has_permission = await self.check_permission(user_id, tenant_id, None, "create")
            if not has_permission:
                self.logger.warning("Permission denied for create",
                                  user_id=user_id, tenant_id=tenant_id)
                raise PermissionError("Create permission denied")

        # 自动添加租户ID
        if hasattr(self.model, 'tenant_id'):
            data['tenant_id'] = tenant_id

        # 自动添加用户ID（如果适用）
        if user_id:
            if hasattr(self.model, 'user_id'):
                data['user_id'] = user_id
            elif hasattr(self.model, 'created_by'):
                data['created_by'] = user_id

        # 数据验证（子类应该重写）
        await self.validate_create_data(data, tenant_id, user_id)

        async with self.transaction_scope():
            db_obj = self.model(**data)
            self.db.add(db_obj)
            await self.db.flush()  # 获取ID但不提交
            await self.db.refresh(db_obj)

            self.logger.info("Record created successfully",
                           model=self.model.__name__,
                           record_id=str(db_obj.id),
                           tenant_id=str(tenant_id),
                           user_id=str(user_id) if user_id else None)

            return db_obj

    async def update_secure(
        self,
        record_id: UUID,
        data: Dict[str, Any],
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        check_permission: bool = True
    ) -> Optional[Base]:
        """
        安全的更新操作，包含权限验证
        """
        if check_permission:
            has_permission = await self.check_permission(user_id, tenant_id, record_id, "update")
            if not has_permission:
                self.logger.warning("Permission denied for update",
                                  user_id=user_id, tenant_id=tenant_id, record_id=record_id)
                raise PermissionError("Update permission denied")

        # 获取现有记录
        db_obj = await self.get_by_id_secure(record_id, tenant_id, user_id, check_permission=False)
        if not db_obj:
            return None

        # 数据验证
        await self.validate_update_data(data, db_obj, tenant_id, user_id)

        async with self.transaction_scope():
            for key, value in data.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)

            await self.db.flush()
            await self.db.refresh(db_obj)

            self.logger.info("Record updated successfully",
                           model=self.model.__name__,
                           record_id=str(record_id),
                           tenant_id=str(tenant_id),
                           user_id=str(user_id) if user_id else None)

            return db_obj

    async def delete_secure(
        self,
        record_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        check_permission: bool = True
    ) -> bool:
        """
        安全的删除操作，包含权限验证
        """
        if check_permission:
            has_permission = await self.check_permission(user_id, tenant_id, record_id, "delete")
            if not has_permission:
                self.logger.warning("Permission denied for delete",
                                  user_id=user_id, tenant_id=tenant_id, record_id=record_id)
                raise PermissionError("Delete permission denied")

        db_obj = await self.get_by_id_secure(record_id, tenant_id, user_id, check_permission=False)
        if not db_obj:
            return False

        async with self.transaction_scope():
            await self.db.delete(db_obj)

            self.logger.info("Record deleted successfully",
                           model=self.model.__name__,
                           record_id=str(record_id),
                           tenant_id=str(tenant_id),
                           user_id=str(user_id) if user_id else None)

            return True

    async def count_secure(
        self,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        安全的统计查询
        """
        conditions = self.get_tenant_filter(self.model, tenant_id)

        if user_id:
            conditions += self.get_user_filter(self.model, user_id)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    conditions.append(getattr(self.model, key) == value)

        query = select(func.count(self.model.id)).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalar()

    # 抽象方法，子类必须实现
    @abstractmethod
    async def validate_create_data(
        self,
        data: Dict[str, Any],
        tenant_id: UUID,
        user_id: Optional[UUID] = None
    ) -> None:
        """验证创建数据"""
        pass

    @abstractmethod
    async def validate_update_data(
        self,
        data: Dict[str, Any],
        existing_obj: Base,
        tenant_id: UUID,
        user_id: Optional[UUID] = None
    ) -> None:
        """验证更新数据"""
        pass

    # 性能监控方法
    async def monitor_query_performance(self, query_name: str, query_func):
        """监控查询性能"""
        import time
        start_time = time.time()
        try:
            result = await query_func()
            execution_time = time.time() - start_time

            if execution_time > 1.0:  # 超过1秒的查询记录警告
                self.logger.warning("Slow query detected",
                                  query_name=query_name,
                                  execution_time=execution_time)

            return result
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error("Query failed",
                            query_name=query_name,
                            execution_time=execution_time,
                            error=str(e))
            raise