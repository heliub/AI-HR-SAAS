"""
Initialize database with initial data
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import init_db, async_session_maker
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import security_manager


async def create_initial_data():
    """创建初始数据"""
    await init_db()
    
    async with async_session_maker() as db:
        # 创建默认租户
        tenant = Tenant(
            name="Default Tenant",
            code="default",
            status="active"
        )
        db.add(tenant)
        await db.flush()
        
        # 创建管理员用户
        admin_user = User(
            tenant_id=tenant.id,
            username="admin",
            email="admin@example.com",
            password_hash=security_manager.hash_password("admin123"),
            full_name="System Administrator",
            role="admin",
            language="en",
            status="active"
        )
        db.add(admin_user)
        
        # 创建测试HR用户
        hr_user = User(
            tenant_id=tenant.id,
            username="hr_user",
            email="hr@example.com",
            password_hash=security_manager.hash_password("hr123"),
            full_name="HR Manager",
            role="hr",
            language="en",
            status="active"
        )
        db.add(hr_user)
        
        await db.commit()
        
        print("✅ Initial data created successfully!")
        print(f"Tenant: {tenant.name} (ID: {tenant.id})")
        print(f"Admin User: {admin_user.email} / admin123")
        print(f"HR User: {hr_user.email} / hr123")


if __name__ == "__main__":
    asyncio.run(create_initial_data())

