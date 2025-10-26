"""
Job service
"""
import re
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.services.base import BaseService
from app.core.exceptions import NotFoundException


class JobService(BaseService[Job]):
    """职位服务"""
    
    def __init__(self):
        super().__init__(Job)
    
    @staticmethod
    def parse_salary(salary_str: str) -> tuple[Optional[int], Optional[int]]:
        """
        解析薪资字符串，如 "30K-50K", "25K+", "面议" 等
        返回 (min_salary, max_salary) 的元组，单位为元/月
        """
        if not salary_str:
            return None, None
        
        # 匹配 "30K-50K" 格式
        match = re.match(r'(\d+)K?-(\d+)K?', salary_str, re.IGNORECASE)
        if match:
            min_k = int(match.group(1))
            max_k = int(match.group(2))
            return min_k * 1000, max_k * 1000
        
        # 匹配 "30K+" 格式
        match = re.match(r'(\d+)K?\+', salary_str, re.IGNORECASE)
        if match:
            min_k = int(match.group(1))
            return min_k * 1000, None
        
        # 匹配纯数字 "30K" 格式
        match = re.match(r'(\d+)K?', salary_str, re.IGNORECASE)
        if match:
            k = int(match.group(1))
            return k * 1000, k * 1000
        
        return None, None
    
    async def get_jobs(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        *,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        status: Optional[str] = None,
        department: Optional[str] = None
    ) -> tuple[List[Job], int]:
        """获取职位列表"""
        query = select(Job).where(Job.tenant_id == tenant_id)
        
        # 搜索条件
        if search:
            query = query.where(
                or_(
                    Job.title.ilike(f"%{search}%"),
                    Job.description.ilike(f"%{search}%")
                )
            )
        
        # 状态筛选
        if status:
            query = query.where(Job.status == status)
        
        # 部门筛选
        if department:
            query = query.where(Job.department == department)
        
        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # 分页
        query = query.order_by(Job.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        return list(jobs), total or 0
    
    async def create_job(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        created_by: UUID,
        **job_data
    ) -> Job:
        """创建职位"""
        # 处理 salary 字段
        if "salary" in job_data and job_data["salary"]:
            min_salary, max_salary = self.parse_salary(job_data["salary"])
            if min_salary:
                job_data["min_salary"] = min_salary
            if max_salary:
                job_data["max_salary"] = max_salary
            # 移除 salary 字段，因为数据库中没有这个字段
            del job_data["salary"]
        
        job_data.update({
            "tenant_id": tenant_id,
            "created_by": created_by
        })
        
        job = Job(**job_data)
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        return job
    
    async def update_job(
        self,
        db: AsyncSession,
        job_id: UUID,
        **update_data
    ) -> Job:
        """更新职位"""
        job = await self.get(db, job_id)
        if not job:
            raise NotFoundException("Job not found")
        
        # 处理 salary 字段
        if "salary" in update_data and update_data["salary"]:
            min_salary, max_salary = self.parse_salary(update_data["salary"])
            if min_salary:
                update_data["min_salary"] = min_salary
            if max_salary:
                update_data["max_salary"] = max_salary
            # 移除 salary 字段，因为数据库中没有这个字段
            del update_data["salary"]
        
        for key, value in update_data.items():
            if value is not None:
                setattr(job, key, value)
        
        await db.commit()
        await db.refresh(job)
        
        return job
    
    async def duplicate_job(
        self,
        db: AsyncSession,
        job_id: UUID,
        created_by: UUID
    ) -> Job:
        """复制职位"""
        original_job = await self.get(db, job_id)
        if not original_job:
            raise NotFoundException("Job not found")
        
        # 创建新职位
        new_job_data = {
            "tenant_id": original_job.tenant_id,
            "title": f"{original_job.title} (副本)",
            "department": original_job.department,
            "location": original_job.location,
            "type": original_job.type,
            "status": "draft",
            "min_salary": original_job.min_salary,
            "max_salary": original_job.max_salary,
            "description": original_job.description,
            "requirements": original_job.requirements,
            "preferred_schools": original_job.preferred_schools,
            "recruitment_invitation": original_job.recruitment_invitation,
            "min_age": original_job.min_age,
            "max_age": original_job.max_age,
            "gender": original_job.gender,
            "education": original_job.education,
            "job_level": original_job.job_level,
            "created_by": created_by
        }
        
        new_job = Job(**new_job_data)
        db.add(new_job)
        await db.commit()
        await db.refresh(new_job)
        
        return new_job
