"""
Resume service
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.services.base import BaseService


class ResumeService(BaseService[Resume]):
    """简历服务"""
    
    def __init__(self):
        super().__init__(Resume)
    
    async def get_resumes(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        *,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        status: Optional[str] = None,
        job_id: Optional[UUID] = None
    ) -> tuple[List[Resume], int]:
        """获取简历列表"""
        query = select(Resume).where(Resume.tenant_id == tenant_id)
        
        # 搜索条件
        if search:
            query = query.where(
                or_(
                    Resume.candidate_name.ilike(f"%{search}%"),
                    Resume.email.ilike(f"%{search}%"),
                    Resume.position.ilike(f"%{search}%")
                )
            )
        
        # 状态筛选
        if status:
            query = query.where(Resume.status == status)
        
        # 职位筛选
        if job_id:
            query = query.where(Resume.job_id == job_id)
        
        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # 分页
        query = query.order_by(Resume.submitted_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        resumes = result.scalars().all()
        
        return list(resumes), total or 0
    
    async def create_resume(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        **resume_data
    ) -> Resume:
        """创建简历"""
        resume_data.update({"tenant_id": tenant_id})
        
        resume = Resume(**resume_data)
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        
        return resume
    
    async def update_resume(
        self,
        db: AsyncSession,
        resume_id: UUID,
        **update_data
    ) -> Resume:
        """更新简历"""
        resume = await self.get(db, resume_id)
        if not resume:
            from app.core.exceptions import NotFoundException
            raise NotFoundException("Resume not found")
        
        for key, value in update_data.items():
            if value is not None:
                setattr(resume, key, value)
        
        await db.commit()
        await db.refresh(resume)
        
        return resume
