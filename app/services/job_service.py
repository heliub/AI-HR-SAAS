"""
Job service for handling job-related database operations
"""
import re
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, func, text, outerjoin

from app.models.job import Job
from app.models.resume import Resume
from app.models.ai_match_result import AIMatchResult
from app.models.recruitment_task import RecruitmentTask
from app.models.job_channel import JobChannel
from app.models.user import User
from app.models.tenant import Tenant
from app.services.base_service import BaseService


class JobService(BaseService):
    """职位服务类，处理职位相关的数据库操作"""

    def __init__(self, db: Optional[AsyncSession] = None):
        super().__init__(db)

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

    async def get_job_with_details(self, job_id: UUID, tenant_id: UUID) -> Optional[Dict]:
        """
        获取职位完整信息，包括统计数据

        Args:
            job_id: 职位ID
            tenant_id: 租户ID

        Returns:
            包含职位完整信息的字典
        """
        job = await self.get_by_id(Job, job_id, tenant_id)
        if not job:
            return None

        # 获取简历统计
        resume_query = select(Resume).where(
            and_(
                Resume.job_id == job_id,
                Resume.tenant_id == tenant_id
            )
        )
        resume_result = await self.db.execute(resume_query)
        resumes = resume_result.scalars().all()

        # 计算简历状态统计
        resume_stats = {"total": len(resumes), "by_status": {}}
        for resume in resumes:
            status = resume.status
            resume_stats["by_status"][status] = resume_stats["by_status"].get(status, 0) + 1

        # 获取AI匹配结果
        match_query = select(AIMatchResult).where(
            and_(
                AIMatchResult.job_id == job_id,
                AIMatchResult.tenant_id == tenant_id
            )
        )
        match_result = await self.db.execute(match_query)
        match_results = match_result.scalars().all()

        # 获取招聘任务
        task_query = select(RecruitmentTask).where(
            and_(
                RecruitmentTask.job_id == job_id,
                RecruitmentTask.tenant_id == tenant_id
            )
        )
        task_result = await self.db.execute(task_query)
        recruitment_tasks = task_result.scalars().all()

        # 获取发布渠道
        channel_query = select(JobChannel).where(
            and_(
                JobChannel.job_id == job_id,
                JobChannel.tenant_id == tenant_id
            )
        )
        channel_result = await self.db.execute(channel_query)
        job_channels = channel_result.scalars().all()

        return {
            "job": job,
            "resume_stats": resume_stats,
            "match_results": match_results,
            "recruitment_tasks": recruitment_tasks,
            "job_channels": job_channels
        }

    async def get_job_with_creator(self, job_id: UUID, tenant_id: UUID) -> Optional[Dict]:
        """
        获取职位及其创建者信息

        Args:
            job_id: 职位ID
            tenant_id: 租户ID

        Returns:
            包含职位和创建者信息的字典
        """
        job = await self.get_by_id(Job, job_id, tenant_id)
        if not job:
            return None

        result = {"job": job}

        # 获取创建者信息
        if job.created_by:
            creator_query = select(User).where(
                and_(
                    User.id == job.created_by,
                    User.tenant_id == tenant_id
                )
            )
            creator_result = await self.db.execute(creator_query)
            creator = creator_result.scalar()
            result["creator"] = creator

        # 获取租户信息
        if job.tenant_id:
            tenant_query = select(Tenant).where(Tenant.id == job.tenant_id)
            tenant_result = await self.db.execute(tenant_query)
            tenant = tenant_result.scalar()
            result["tenant"] = tenant

        return result

    async def get_jobs_with_resume_count(self, tenant_id: UUID, skip: int = 0, limit: int = 100) -> List[Dict]:
        """
        获取职位列表及其简历数量统计

        Args:
            tenant_id: 租户ID
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            包含职位和简历数量的字典列表
        """
        jobs = await self.get_all(Job, tenant_id, skip, limit)

        result = []
        for job in jobs:
            resume_query = select(func.count(Resume.id)).where(
                and_(
                    Resume.job_id == job.id,
                    Resume.tenant_id == tenant_id
                )
            )
            resume_result = await self.db.execute(resume_query)
            resume_count = resume_result.scalar()

            result.append({
                "job": job,
                "resume_count": resume_count
            })

        return result

    async def search_jobs(
        self,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        company: Optional[str] = None,
        category: Optional[str] = None,
        workplace_type: Optional[str] = None,
        location: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        is_admin: bool = False
    ) -> List[Job]:
        """
        搜索职位

        Args:
            tenant_id: 租户ID
            user_id: 用户ID
            keyword: 搜索关键词（搜索标题、公司、描述）
            status: 职位状态
            company: 公司名称
            category: 职位类别
            workplace_type: 工作场所类型
            location: 工作地点
            skip: 跳过记录数
            limit: 返回记录数
            is_admin: 是否为管理员

        Returns:
            职位列表
        """
        # 构建基础查询
        conditions = [Job.tenant_id == tenant_id]

        # 用户过滤 - 只有非管理员才过滤user_id
        if user_id and not is_admin:
            conditions.append(Job.user_id == user_id)

        if status:
            conditions.append(Job.status == status)

        if company:
            conditions.append(Job.company.ilike(f"%{company}%"))

        if category:
            conditions.append(Job.category.contains([category]))

        if workplace_type:
            conditions.append(Job.workplace_type == workplace_type)

        if location:
            conditions.append(Job.location == location)

        if keyword:
            conditions.append(
                or_(
                    Job.title.ilike(f"%{keyword}%"),
                    Job.company.ilike(f"%{keyword}%"),
                    Job.description.ilike(f"%{keyword}%")
                )
            )

        query = select(Job).where(and_(*conditions)).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_job_statistics(self, tenant_id: UUID) -> Dict:
        """
        获取职位统计信息

        Args:
            tenant_id: 租户ID

        Returns:
            统计信息字典
        """
        # 获取总职位数
        total_query = select(func.count(Job.id)).where(Job.tenant_id == tenant_id)
        total_result = await self.db.execute(total_query)
        total_jobs = total_result.scalar()

        # 获取各状态的职位数
        status_stats = {}
        for status in ['draft', 'open', 'closed']:
            status_query = select(func.count(Job.id)).where(
                and_(
                    Job.tenant_id == tenant_id,
                    Job.status == status
                )
            )
            status_result = await self.db.execute(status_query)
            status_count = status_result.scalar()
            status_stats[status] = status_count

        return {
            "total": total_jobs,
            "by_status": status_stats
        }

    async def create_job(self, tenant_id: UUID, user_id: UUID, created_by: UUID, job_data: Dict) -> Job:
        """
        创建新职位

        Args:
            tenant_id: 租户ID
            user_id: 用户ID
            created_by: 创建人ID
            job_data: 职位数据

        Returns:
            创建的职位对象
        """
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
            "user_id": user_id,
            "created_by": created_by
        })

        return await self.create(Job, job_data)

    async def update_job_status(self, job_id: UUID, tenant_id: UUID, status: str) -> Optional[Job]:
        """
        更新职位状态

        Args:
            job_id: 职位ID
            tenant_id: 租户ID
            status: 新状态

        Returns:
            更新后的职位对象
        """
        from datetime import datetime

        update_data = {"status": status}

        # 如果状态改为关闭，设置关闭时间
        if status == "closed":
            update_data["closed_at"] = datetime.utcnow()

        # BaseService的update方法会自动更新updated_at字段
        return await self.update(Job, job_id, update_data, tenant_id)

    async def count_jobs(
        self,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        filters: Optional[Dict[str, Any]] = None,
        is_admin: bool = False
    ) -> int:
        """
        统计职位数量（自动过滤已删除的职位）

        Args:
            tenant_id: 租户ID
            user_id: 用户ID
            filters: 过滤条件
            is_admin: 是否为管理员

        Returns:
            职位数量
        """
        conditions = [Job.tenant_id == tenant_id]

        # 默认过滤已删除的职位，除非明确查询已删除状态
        status = filters.get('status') if filters else None
        if status != "deleted":
            conditions.append(Job.status != "deleted")

        # 用户过滤 - 只有非管理员才过滤user_id
        if user_id and not is_admin:
            conditions.append(Job.user_id == user_id)

        if filters:
            for key, value in filters.items():
                if hasattr(Job, key) and value is not None:
                    if key == 'company':
                        conditions.append(Job.company.ilike(f"%{value}%"))
                    elif key == 'category':
                        conditions.append(Job.category.contains([value]))
                    elif key == 'workplace_type':
                        conditions.append(Job.workplace_type == value)
                    else:
                        conditions.append(getattr(Job, key) == value)

        query = select(func.count(Job.id)).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalar()

    async def duplicate_job(self, job_id: UUID, tenant_id: UUID, user_id: UUID, created_by: UUID) -> Optional[Job]:
        """
        复制职位

        Args:
            job_id: 原职位ID
            tenant_id: 租户ID
            user_id: 用户ID
            created_by: 创建人ID

        Returns:
            新职位对象
        """
        original_job = await self.get_by_id(Job, job_id, tenant_id)
        if not original_job:
            return None

        # 创建新职位
        new_job_data = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "title": f"{original_job.title} (副本)",
            "company": original_job.company,
            "location": original_job.location,
            "type": original_job.type,
            "workplace_type": original_job.workplace_type,
            "status": "draft",
            "min_salary": original_job.min_salary,
            "max_salary": original_job.max_salary,
            "pay_type": original_job.pay_type,
            "pay_currency": original_job.pay_currency,
            "pay_shown_on_ad": original_job.pay_shown_on_ad,
            "description": original_job.description,
            "requirements": original_job.requirements,
            "preferred_schools": original_job.preferred_schools,
            "category": original_job.category,
            "recruitment_invitation": original_job.recruitment_invitation,
            "education": original_job.education,
            "created_by": created_by
        }

        return await self.create(Job, new_job_data)

    async def search_jobs_with_channels(
        self,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        company: Optional[str] = None,
        category: Optional[str] = None,
        workplace_type: Optional[str] = None,
        location: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        is_admin: bool = False
    ) -> Dict[str, List]:
        """
        优化版本：使用JOIN查询一次性获取职位及其关联的渠道，解决N+1查询问题

        Args:
            tenant_id: 租户ID
            user_id: 用户ID
            keyword: 搜索关键词（搜索标题、公司、描述）
            status: 职位状态
            company: 公司名称
            category: 职位类别
            workplace_type: 工作场所类型
            location: 工作地点
            skip: 跳过记录数
            limit: 返回记录数
            is_admin: 是否为管理员

        Returns:
            包含职位列表和渠道映射的字典: {"jobs": List[Job], "job_channels": Dict[UUID, List[UUID]]}
        """
        # 构建基础查询条件
        conditions = [Job.tenant_id == tenant_id]

        # 默认过滤已删除的职位，除非明确查询已删除状态
        if status != "deleted":
            conditions.append(Job.status != "deleted")

        # 用户过滤 - 只有非管理员才过滤user_id
        if user_id and not is_admin:
            conditions.append(Job.user_id == user_id)

        if status:
            conditions.append(Job.status == status)

        if company:
            conditions.append(Job.company.ilike(f"%{company}%"))

        if category:
            conditions.append(Job.category.contains([category]))

        if workplace_type:
            conditions.append(Job.workplace_type == workplace_type)

        if location:
            conditions.append(Job.location == location)

        if keyword:
            conditions.append(
                or_(
                    Job.title.ilike(f"%{keyword}%"),
                    Job.company.ilike(f"%{keyword}%"),
                    Job.description.ilike(f"%{keyword}%")
                )
            )

        # 使用LEFT JOIN获取职位和渠道信息
        query = (
            select(Job, JobChannel.channel_id)
            .select_from(Job)
            .outerjoin(JobChannel, and_(
                Job.id == JobChannel.job_id,
                JobChannel.tenant_id == tenant_id
            ))
            .where(and_(*conditions))
            .offset(skip)
            .limit(limit)
            .order_by(Job.created_at.desc())
        )

        result = await self.db.execute(query)
        rows = result.all()

        # 组织结果：职位列表和渠道映射
        jobs_dict = {}
        job_channels = {}

        for job, channel_id in rows:
            job_id = job.id

            # 如果职位还没有被记录，添加到职位字典
            if job_id not in jobs_dict:
                jobs_dict[job_id] = job
                job_channels[job_id] = []

            # 如果有渠道ID，添加到渠道列表
            if channel_id:
                job_channels[job_id].append(channel_id)

        # 转换为最终的返回格式
        jobs_list = list(jobs_dict.values())

        return {
            "jobs": jobs_list,
            "job_channels": job_channels
        }