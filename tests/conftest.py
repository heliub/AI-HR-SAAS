"""
Pytest configuration and fixtures
"""
import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.models.base import Base
from app.models import Tenant, User, Job, Resume
from app.infrastructure.database.session import get_db
from app.core.security import security_manager

# 测试数据库URL - 使用PostgreSQL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgrespw@localhost:55000/postgres"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)
    #     await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # 默认保留测试数据，只有设置了DELETE_TEST_DATA=1环境变量时才删除
    # if os.getenv("DELETE_TEST_DATA"):
    #     async with engine.begin() as conn:
    #         await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话"""
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_tenant(db_session: AsyncSession) -> Tenant:
    """创建测试租户"""
    tenant = Tenant(
        name="测试公司",
        company_name="Test Company Ltd.",
        contact_email="test@example.com",
        plan_type="pro",
        status="active",
        max_users=50,
        max_jobs=100
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def test_user(db_session: AsyncSession, test_tenant: Tenant) -> User:
    """创建测试用户"""
    user = User(
        tenant_id=test_tenant.id,
        name="测试用户",
        email="test@example.com",
        password_hash=security_manager.hash_password("password123"),
        role="admin",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user: User) -> str:
    """生成认证Token"""
    token = security_manager.create_access_token(
        data={
            "sub": str(test_user.id),
            "tenantId": str(test_user.tenant_id),
            "role": test_user.role
        }
    )
    return token


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """生成认证请求头"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
async def test_job(db_session: AsyncSession, test_tenant: Tenant, test_user: User) -> Job:
    """创建测试职位"""
    job = Job(
        tenant_id=test_tenant.id,
        title="高级前端工程师",
        department="技术部",
        location="北京",
        type="full-time",
        status="open",
        min_salary=25000,
        max_salary=40000,
        description="负责公司核心产品的前端开发工作",
        requirements="5年以上前端开发经验,精通React/Vue",
        preferred_schools="清华大学,北京大学",
        education="本科及以上",
        min_age=25,
        max_age=35,
        created_by=test_user.id
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job


@pytest.fixture
async def test_resume(db_session: AsyncSession, test_tenant: Tenant, test_job: Job) -> Resume:
    """创建测试简历"""
    resume = Resume(
        tenant_id=test_tenant.id,
        candidate_name="张伟",
        email="zhangwei@example.com",
        phone="13800138000",
        position="高级前端工程师",
        status="pending",
        source="智联招聘",
        job_id=test_job.id,
        experience_years="6年",
        education_level="本科",
        age=29,
        gender="male",
        location="北京",
        school="北京大学",
        major="计算机科学与技术",
        skills="React,TypeScript,Node.js"
    )
    db_session.add(resume)
    await db_session.commit()
    await db_session.refresh(resume)
    return resume

