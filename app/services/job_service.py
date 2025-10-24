"""
Job service
"""
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job
from app.services.base import BaseService


class JobService(BaseService[Job]):
    """职位服务"""
    
    def __init__(self):
        super().__init__(Job)
    
    async def create_job(
        self,
        db: AsyncSession,
        tenant_id: int,
        created_by: int,
        **job_data
    ) -> Job:
        """创建职位"""
        job_data.update({
            "tenant_id": tenant_id,
            "created_by": created_by,
            "status": "open"
        })
        
        job = await self.repository.create(db, job_data)
        await db.commit()
        await db.refresh(job)
        
        return job
    
    async def get_open_jobs(
        self,
        db: AsyncSession,
        tenant_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Job]:
        """获取开放职位列表"""
        query = select(Job).where(
            Job.tenant_id == tenant_id,
            Job.status == "open"
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())

