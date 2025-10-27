"""
Resume service for handling resume-related database operations
"""
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, func

from app.models.resume import Resume
from app.models.work_experience import WorkExperience
from app.models.project_experience import ProjectExperience
from app.models.education_history import EducationHistory
from app.models.job_preference import JobPreference
from app.models.ai_match_result import AIMatchResult
from app.models.candidate_chat_history import CandidateChatHistory
from app.models.interview import Interview
from app.models.email_log import EmailLog
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.channel import Channel
from app.services.base_service import BaseService


class ResumeService(BaseService):
    """简历服务类，处理简历相关的数据库操作"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_resume_full_details(self, resume_id: UUID, tenant_id: UUID) -> Optional[Dict]:
        """
        获取简历完整详情，包括所有关联数据

        🚨 性能警告：这个方法存在严重的N+1查询问题！
        在生产环境中，请使用优化版本 get_resume_full_details_optimized

        Args:
            resume_id: 简历ID
            tenant_id: 租户ID

        Returns:
            包含简历完整信息的字典
        """
        # TODO: 这个方法性能极差，请使用 get_resume_full_details_optimized
        logger.warning("Using deprecated slow method get_resume_full_details",
                      resume_id=resume_id, tenant_id=tenant_id)

        resume = await self.get_by_id(Resume, resume_id, tenant_id)
        if not resume:
            return None

        # 🚨 这里执行了8次独立查询，严重性能问题！
        work_query = select(WorkExperience).where(
            and_(
                WorkExperience.resume_id == resume_id,
                WorkExperience.tenant_id == tenant_id
            )
        )
        work_result = await self.db.execute(work_query)
        work_experiences = work_result.scalars().all()

        project_query = select(ProjectExperience).where(
            and_(
                ProjectExperience.resume_id == resume_id,
                ProjectExperience.tenant_id == tenant_id
            )
        )
        project_result = await self.db.execute(project_query)
        project_experiences = project_result.scalars().all()

        education_query = select(EducationHistory).where(
            and_(
                EducationHistory.resume_id == resume_id,
                EducationHistory.tenant_id == tenant_id
            )
        )
        education_result = await self.db.execute(education_query)
        education_histories = education_result.scalars().all()

        job_pref_query = select(JobPreference).where(
            and_(
                JobPreference.resume_id == resume_id,
                JobPreference.tenant_id == tenant_id
            )
        )
        job_pref_result = await self.db.execute(job_pref_query)
        job_preference = job_pref_result.scalar()

        ai_match_query = select(AIMatchResult).where(
            and_(
                AIMatchResult.resume_id == resume_id,
                AIMatchResult.tenant_id == tenant_id
            )
        )
        ai_match_result = await self.db.execute(ai_match_query)
        ai_match_results = ai_match_result.scalars().all()

        chat_query = select(CandidateChatHistory).where(
            and_(
                CandidateChatHistory.resume_id == resume_id,
                CandidateChatHistory.tenant_id == tenant_id
            )
        ).order_by(CandidateChatHistory.created_at.desc())
        chat_result = await self.db.execute(chat_query)
        chat_history = chat_result.scalars().all()

        interview_query = select(Interview).where(
            and_(
                Interview.candidate_id == resume_id,  # 注意：这里用的是candidate_id关联到resume
                Interview.tenant_id == tenant_id
            )
        )
        interview_result = await self.db.execute(interview_query)
        interviews = interview_result.scalars().all()

        email_query = select(EmailLog).where(
            and_(
                EmailLog.resume_id == resume_id,
                EmailLog.tenant_id == tenant_id
            )
        ).order_by(EmailLog.created_at.desc())
        email_result = await self.db.execute(email_query)
        email_logs = email_result.scalars().all()

        return {
            "resume": resume,
            "work_experiences": work_experiences,
            "project_experiences": project_experiences,
            "education_histories": education_histories,
            "job_preference": job_preference,
            "ai_match_results": ai_match_results,
            "chat_history": chat_history,
            "interviews": interviews,
            "email_logs": email_logs
        }

    async def get_resume_with_job_and_candidate(self, resume_id: UUID, tenant_id: UUID) -> Optional[Dict]:
        """
        获取简历及其关联的职位和候选人信息

        Args:
            resume_id: 简历ID
            tenant_id: 租户ID

        Returns:
            包含简历、职位和候选人信息的字典
        """
        resume = await self.get_by_id(Resume, resume_id, tenant_id)
        if not resume:
            return None

        result = {"resume": resume}

        # 获取关联的职位信息
        if resume.job_id:
            job_query = select(Job).where(
                and_(
                    Job.id == resume.job_id,
                    Job.tenant_id == tenant_id
                )
            )
            job_result = await self.db.execute(job_query)
            job = job_result.scalar()
            result["job"] = job

        # 获取关联的候选人信息（如果存在的话）
        # 注意：根据数据库设计，一个简历可能关联一个候选人
        # 但这里的逻辑可能需要根据实际业务需求调整
        result["candidate"] = None  # 暂时设为None，因为resumes表没有直接关联candidates

        # 获取来源渠道信息
        if resume.source_channel_id:
            channel_query = select(Channel).where(
                and_(
                    Channel.id == resume.source_channel_id,
                    Channel.tenant_id == tenant_id
                )
            )
            channel_result = await self.db.execute(channel_query)
            channel = channel_result.scalar()
            result["source_channel"] = channel

        return result

    async def get_resumes_by_job(self, job_id: UUID, tenant_id: UUID, status: Optional[str] = None) -> List[Resume]:
        """
        获取特定职位的所有简历

        Args:
            job_id: 职位ID
            tenant_id: 租户ID
            status: 简历状态过滤

        Returns:
            简历列表
        """
        conditions = [
            Resume.job_id == job_id,
            Resume.tenant_id == tenant_id
        ]

        if status:
            conditions.append(Resume.status == status)

        query = select(Resume).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_resumes_by_candidate(self, resume_id: UUID, tenant_id: UUID) -> List[Resume]:
        """
        根据简历ID获取该简历（这个方法名可能不太准确，实际是根据简历ID）

        Args:
            resume_id: 简历ID（不是候选人ID）
            tenant_id: 租户ID

        Returns:
            简历列表
        """
        query = select(Resume).where(
            and_(
                Resume.id == resume_id,
                Resume.tenant_id == tenant_id
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def search_resumes(
        self,
        tenant_id: UUID,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        job_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Resume]:
        """
        搜索简历

        Args:
            tenant_id: 租户ID
            keyword: 搜索关键词（搜索姓名、邮箱、职位）
            status: 简历状态
            job_id: 职位ID
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            简历列表
        """
        conditions = [Resume.tenant_id == tenant_id]

        if status:
            conditions.append(Resume.status == status)

        if job_id:
            conditions.append(Resume.job_id == job_id)

        if keyword:
            conditions.append(
                or_(
                    Resume.candidate_name.ilike(f"%{keyword}%"),
                    Resume.email.ilike(f"%{keyword}%"),
                    Resume.position.ilike(f"%{keyword}%")
                )
            )

        query = select(Resume).where(and_(*conditions)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def search_resumes_async(self, tenant_id: UUID, keyword: Optional[str] = None,
                                status: Optional[str] = None, job_id: Optional[UUID] = None,
                                skip: int = 0, limit: int = 10) -> List[Resume]:
        """
        异步版本的搜索简历方法

        Args:
            tenant_id: 租户ID
            keyword: 搜索关键词
            status: 简历状态
            job_id: 职位ID
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            简历列表
        """
        from sqlalchemy import select
        stmt = select(Resume).filter(Resume.tenant_id == tenant_id)

        if status:
            stmt = stmt.filter(Resume.status == status)

        if job_id:
            stmt = stmt.filter(Resume.job_id == job_id)

        if keyword:
            stmt = stmt.filter(
                or_(
                    Resume.candidate_name.ilike(f"%{keyword}%"),
                    Resume.email.ilike(f"%{keyword}%"),
                    Resume.position.ilike(f"%{keyword}%")
                )
            )

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count_async(self, model, tenant_id: UUID, filters: Optional[Dict] = None) -> int:
        """
        异步版本的统计方法
        """
        from sqlalchemy import select, func
        stmt = select(func.count(model.id)).filter(model.tenant_id == tenant_id)

        if filters:
            for key, value in filters.items():
                if hasattr(model, key) and value is not None:
                    stmt = stmt.filter(getattr(model, key) == value)

        result = await self.db.execute(stmt)
        return result.scalar()

    async def get_resume_statistics(self, tenant_id: UUID, job_id: Optional[UUID] = None) -> Dict:
        """
        获取简历统计信息

        Args:
            tenant_id: 租户ID
            job_id: 职位ID（可选）

        Returns:
            统计信息字典
        """
        conditions = [Resume.tenant_id == tenant_id]
        if job_id:
            conditions.append(Resume.job_id == job_id)

        # 获取总数
        total_query = select(func.count(Resume.id)).where(and_(*conditions))
        total_result = await self.db.execute(total_query)
        total = total_result.scalar()

        # 获取各状态统计
        status_stats = {}
        for status in ['pending', 'reviewing', 'interview', 'offered', 'rejected']:
            status_conditions = conditions + [Resume.status == status]
            status_query = select(func.count(Resume.id)).where(and_(*status_conditions))
            status_result = await self.db.execute(status_query)
            status_count = status_result.scalar()
            status_stats[status] = status_count

        return {
            "total": total,
            "by_status": status_stats
        }

    async def create_resume(self, tenant_id: UUID, resume_data: Dict) -> Resume:
        """
        创建新简历

        Args:
            tenant_id: 租户ID
            resume_data: 简历数据

        Returns:
            创建的简历对象
        """
        resume_data["tenant_id"] = tenant_id
        return await self.create(Resume, resume_data)

    async def update_resume_status(self, resume_id: UUID, tenant_id: UUID, status: str) -> Optional[Resume]:
        """
        更新简历状态

        Args:
            resume_id: 简历ID
            tenant_id: 租户ID
            status: 新状态

        Returns:
            更新后的简历对象
        """
        return await self.update(Resume, resume_id, {"status": status}, tenant_id)