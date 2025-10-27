"""
事务管理系统
确保数据一致性和可靠性
"""
import asyncio
from typing import Any, Dict, List, Optional, Callable, AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession, AsyncConnection
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
import structlog

logger = structlog.get_logger(__name__)


class TransactionStatus(Enum):
    """事务状态"""
    PENDING = "pending"
    ACTIVE = "active"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class TransactionContext:
    """事务上下文"""
    session: AsyncSession
    tenant_id: UUID
    user_id: Optional[UUID] = None
    operation_name: str = "unknown"
    start_time: datetime = None
    status: TransactionStatus = TransactionStatus.PENDING
    error: Optional[Exception] = None
    savepoints: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.utcnow()
        if self.savepoints is None:
            self.savepoints = []
        if self.metadata is None:
            self.metadata = {}


class TransactionManager:
    """事务管理器"""

    def __init__(self):
        self.active_transactions: Dict[str, TransactionContext] = {}
        self.max_concurrent_transactions = 100

    @asynccontextmanager
    async def transaction_scope(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        operation_name: str = "unknown",
        isolation_level: Optional[str] = None,
        readonly: bool = False
    ) -> AsyncGenerator[TransactionContext, None]:
        """
        事务作用域管理器

        Args:
            session: 数据库会话
            tenant_id: 租户ID
            user_id: 用户ID
            operation_name: 操作名称
            isolation_level: 隔离级别
            readonly: 是否只读事务

        Yields:
            TransactionContext: 事务上下文
        """
        # 检查并发事务数量限制
        if len(self.active_transactions) >= self.max_concurrent_transactions:
            raise RuntimeError("Too many concurrent transactions")

        transaction_id = f"{tenant_id}_{operation_name}_{datetime.utcnow().timestamp()}"
        context = TransactionContext(
            session=session,
            tenant_id=tenant_id,
            user_id=user_id,
            operation_name=operation_name
        )

        self.active_transactions[transaction_id] = context

        try:
            # 设置事务参数
            if isolation_level:
                await session.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"))

            if readonly:
                await session.execute(text("SET TRANSACTION READ ONLY"))

            # 开始事务
            await session.begin()
            context.status = TransactionStatus.ACTIVE

            logger.info("Transaction started",
                       transaction_id=transaction_id,
                       operation=operation_name,
                       tenant_id=str(tenant_id),
                       user_id=str(user_id) if user_id else None)

            yield context

            # 提交事务
            await session.commit()
            context.status = TransactionStatus.COMMITTED

            logger.info("Transaction committed",
                       transaction_id=transaction_id,
                       operation=operation_name,
                       duration=(datetime.utcnow() - context.start_time).total_seconds())

        except Exception as e:
            # 回滚事务
            try:
                await session.rollback()
                context.status = TransactionStatus.ROLLED_BACK
                context.error = e

                logger.error("Transaction rolled back",
                           transaction_id=transaction_id,
                           operation=operation_name,
                           error=str(e),
                           duration=(datetime.utcnow() - context.start_time).total_seconds())

            except Exception as rollback_error:
                context.status = TransactionStatus.FAILED
                logger.error("Failed to rollback transaction",
                           transaction_id=transaction_id,
                           error=str(rollback_error))

            raise

        finally:
            # 清理事务上下文
            self.active_transactions.pop(transaction_id, None)

    async def create_savepoint(
        self,
        session: AsyncSession,
        name: str
    ) -> str:
        """
        创建保存点

        Args:
            session: 数据库会话
            name: 保存点名称

        Returns:
            str: 保存点名称
        """
        try:
            await session.execute(text(f"SAVEPOINT {name}"))
            logger.info("Savepoint created", savepoint=name)
            return name
        except Exception as e:
            logger.error("Failed to create savepoint", savepoint=name, error=str(e))
            raise

    async def rollback_to_savepoint(
        self,
        session: AsyncSession,
        name: str
    ):
        """
        回滚到保存点

        Args:
            session: 数据库会话
            name: 保存点名称
        """
        try:
            await session.execute(text(f"ROLLBACK TO SAVEPOINT {name}"))
            logger.info("Rolled back to savepoint", savepoint=name)
        except Exception as e:
            logger.error("Failed to rollback to savepoint", savepoint=name, error=str(e))
            raise

    async def release_savepoint(
        self,
        session: AsyncSession,
        name: str
    ):
        """
        释放保存点

        Args:
            session: 数据库会话
            name: 保存点名称
        """
        try:
            await session.execute(text(f"RELEASE SAVEPOINT {name}"))
            logger.info("Savepoint released", savepoint=name)
        except Exception as e:
            logger.error("Failed to release savepoint", savepoint=name, error=str(e))
            raise

    def get_active_transactions(self) -> Dict[str, TransactionContext]:
        """获取活跃事务列表"""
        return self.active_transactions.copy()

    def get_transaction_count(self) -> int:
        """获取活跃事务数量"""
        return len(self.active_transactions)


class BatchProcessor:
    """批量处理器"""

    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size

    async def process_batch(
        self,
        items: List[Any],
        processor: Callable[[List[Any]], Awaitable[None]],
        session: AsyncSession,
        tenant_id: UUID,
        operation_name: str = "batch_process"
    ) -> Dict[str, Any]:
        """
        批量处理数据

        Args:
            items: 要处理的数据列表
            processor: 处理函数
            session: 数据库会话
            tenant_id: 租户ID
            operation_name: 操作名称

        Returns:
            处理结果统计
        """
        total_items = len(items)
        processed_items = 0
        failed_items = 0
        errors = []

        start_time = datetime.utcnow()

        # 分批处理
        for i in range(0, total_items, self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1

            try:
                # 为每个批次创建一个事务
                async with transaction_manager.transaction_scope(
                    session=session,
                    tenant_id=tenant_id,
                    operation_name=f"{operation_name}_batch_{batch_num}"
                ):
                    await processor(batch)
                    processed_items += len(batch)

                logger.info("Batch processed successfully",
                           batch_num=batch_num,
                           batch_size=len(batch),
                           processed_total=processed_items)

            except Exception as e:
                failed_items += len(batch)
                errors.append({
                    'batch_num': batch_num,
                    'batch_size': len(batch),
                    'error': str(e),
                    'items': batch[:5]  # 只记录前5个项目作为示例
                })

                logger.error("Batch processing failed",
                           batch_num=batch_num,
                           batch_size=len(batch),
                           error=str(e))

        duration = (datetime.utcnow() - start_time).total_seconds()

        return {
            'total_items': total_items,
            'processed_items': processed_items,
            'failed_items': failed_items,
            'success_rate': processed_items / total_items if total_items > 0 else 0,
            'duration_seconds': duration,
            'items_per_second': processed_items / duration if duration > 0 else 0,
            'errors': errors
        }


class DistributedLock:
    """分布式锁（基于数据库实现）"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def acquire_lock(
        self,
        lock_key: str,
        timeout_seconds: int = 30,
        owner: str = None
    ) -> bool:
        """
        获取分布式锁

        Args:
            lock_key: 锁的键
            timeout_seconds: 超时时间
            owner: 锁的所有者

        Returns:
            bool: 是否成功获取锁
        """
        try:
            # 尝试插入锁记录
            query = text("""
                INSERT INTO distributed_locks (lock_key, owner, expires_at, created_at)
                VALUES (:lock_key, :owner, :expires_at, :created_at)
                ON CONFLICT (lock_key) DO NOTHING
            """)

            expires_at = datetime.utcnow() + timedelta(seconds=timeout_seconds)
            created_at = datetime.utcnow()

            result = await self.session.execute(query, {
                'lock_key': lock_key,
                'owner': owner or 'unknown',
                'expires_at': expires_at,
                'created_at': created_at
            })

            # 检查是否成功插入
            if result.rowcount > 0:
                logger.info("Lock acquired", lock_key=lock_key, owner=owner)
                return True

            # 检查现有锁是否过期
            await self.cleanup_expired_locks()

            # 再次尝试获取锁
            result = await self.session.execute(query, {
                'lock_key': lock_key,
                'owner': owner or 'unknown',
                'expires_at': expires_at,
                'created_at': created_at
            })

            return result.rowcount > 0

        except Exception as e:
            logger.error("Failed to acquire lock", lock_key=lock_key, error=str(e))
            return False

    async def release_lock(self, lock_key: str, owner: str = None) -> bool:
        """
        释放分布式锁

        Args:
            lock_key: 锁的键
            owner: 锁的所有者

        Returns:
            bool: 是否成功释放锁
        """
        try:
            query = text("""
                DELETE FROM distributed_locks
                WHERE lock_key = :lock_key AND (owner = :owner OR owner IS NULL)
            """)

            result = await self.session.execute(query, {
                'lock_key': lock_key,
                'owner': owner
            })

            if result.rowcount > 0:
                logger.info("Lock released", lock_key=lock_key, owner=owner)
                return True

            return False

        except Exception as e:
            logger.error("Failed to release lock", lock_key=lock_key, error=str(e))
            return False

    async def cleanup_expired_locks(self):
        """清理过期的锁"""
        try:
            query = text("""
                DELETE FROM distributed_locks
                WHERE expires_at < :now
            """)

            result = await self.session.execute(query, {'now': datetime.utcnow()})
            logger.info("Expired locks cleaned up", count=result.rowcount)

        except Exception as e:
            logger.error("Failed to cleanup expired locks", error=str(e))

    @asynccontextmanager
    async def lock(
        self,
        lock_key: str,
        timeout_seconds: int = 30,
        owner: str = None
    ):
        """分布式锁上下文管理器"""
        if await self.acquire_lock(lock_key, timeout_seconds, owner):
            try:
                yield
            finally:
                await self.release_lock(lock_key, owner)
        else:
            raise RuntimeError(f"Failed to acquire lock: {lock_key}")


# 全局事务管理器
transaction_manager = TransactionManager()


# 事务装饰器
def transactional(operation_name: str = None, readonly: bool = False):
    """事务装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中提取必要信息
            session = kwargs.get('db') or getattr(args[0] if args else None, 'db', None)
            tenant_id = kwargs.get('tenant_id') or getattr(args[0] if args else None, 'tenant_id', None)
            user_id = kwargs.get('user_id') or getattr(args[0] if args else None, 'user_id', None)

            if not session or not tenant_id:
                raise ValueError("Session and tenant_id are required for transaction")

            op_name = operation_name or f"{func.__module__}.{func.__name__}"

            async with transaction_manager.transaction_scope(
                session=session,
                tenant_id=tenant_id,
                user_id=user_id,
                operation_name=op_name,
                readonly=readonly
            ):
                return await func(*args, **kwargs)

        return wrapper
    return decorator


# 数据一致性检查器
class ConsistencyChecker:
    """数据一致性检查器"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_resume_candidate_consistency(self, tenant_id: UUID) -> Dict[str, Any]:
        """检查简历和候选人数据一致性"""
        try:
            # 检查孤立的简历（没有对应的候选人）
            orphan_resumes_query = text("""
                SELECT COUNT(*) as count
                FROM resumes r
                LEFT JOIN candidates c ON r.candidate_id = c.id
                WHERE r.tenant_id = :tenant_id AND r.candidate_id IS NOT NULL AND c.id IS NULL
            """)
            result = await self.session.execute(orphan_resumes_query, {'tenant_id': str(tenant_id)})
            orphan_resumes = result.scalar()

            # 检查孤立的候选人（没有简历）
            orphan_candidates_query = text("""
                SELECT COUNT(*) as count
                FROM candidates c
                LEFT JOIN resumes r ON c.id = r.candidate_id
                WHERE c.tenant_id = :tenant_id AND r.id IS NULL
            """)
            result = await self.session.execute(orphan_candidates_query, {'tenant_id': str(tenant_id)})
            orphan_candidates = result.scalar()

            return {
                'orphan_resumes': orphan_resumes,
                'orphan_candidates': orphan_candidates,
                'consistent': orphan_resumes == 0 and orphan_candidates == 0
            }

        except Exception as e:
            logger.error("Consistency check failed", error=str(e))
            return {'error': str(e), 'consistent': False}

    async def check_job_resume_consistency(self, tenant_id: UUID) -> Dict[str, Any]:
        """检查职位和简历数据一致性"""
        try:
            # 检查孤立的简历（引用不存在的职位）
            orphan_resumes_query = text("""
                SELECT COUNT(*) as count
                FROM resumes r
                LEFT JOIN jobs j ON r.job_id = j.id
                WHERE r.tenant_id = :tenant_id AND r.job_id IS NOT NULL AND j.id IS NULL
            """)
            result = await self.session.execute(orphan_resumes_query, {'tenant_id': str(tenant_id)})
            orphan_resumes = result.scalar()

            return {
                'orphan_resumes': orphan_resumes,
                'consistent': orphan_resumes == 0
            }

        except Exception as e:
            logger.error("Consistency check failed", error=str(e))
            return {'error': str(e), 'consistent': False}