"""
Database session management
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings

# 全局引擎实例
engine: AsyncEngine = None
async_session_maker: async_sessionmaker[AsyncSession] = None


async def init_db() -> None:
    """初始化数据库连接"""
    global engine, async_session_maker
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={
            "server_settings": {
                "application_name": "hr_saas",
                "jit": "off",
            },
            "command_timeout": 60,
            "timeout": 10,
        },
    )
    
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def close_db() -> None:
    """关闭数据库连接"""
    global engine
    if engine:
        await engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    
    使用示例:
        async with get_db() as db:
            # 使用db进行数据库操作
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

