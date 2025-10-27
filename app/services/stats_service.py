"""
Stats service
"""
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.models.job import Job
from app.models.channel import Channel
from app.models.interview import Interview
from app.models.recruitment_task import RecruitmentTask
from app.models.chat_message import ChatMessage
from app.models.ai_match_result import AIMatchResult


class StatsService:
    """统计数据服务"""

    async def get_dashboard_stats(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """获取Dashboard统计数据"""
        base_filters = [Resume.tenant_id == tenant_id]
        if user_id:
            base_filters.append(Resume.user_id == user_id)

        # 待处理简历数
        pending_resumes_query = select(func.count()).select_from(
            Resume.__table__.where(and_(*base_filters, Resume.status == "pending"))
        )
        pending_resumes = await db.scalar(pending_resumes_query)

        # 即将到来的面试数（未来7天）
        now = datetime.utcnow().date()
        week_later = now + timedelta(days=7)

        interview_filters = [Interview.tenant_id == tenant_id]
        if user_id:
            interview_filters.append(Interview.user_id == user_id)

        upcoming_interviews_query = select(func.count()).select_from(
            Interview.__table__.where(
                and_(
                    *interview_filters,
                    Interview.status == "scheduled",
                    Interview.interview_date >= now,
                    Interview.interview_date <= week_later
                )
            )
        )
        upcoming_interviews = await db.scalar(upcoming_interviews_query)

        # 活跃任务数
        task_filters = [RecruitmentTask.tenant_id == tenant_id]
        if user_id:
            task_filters.append(RecruitmentTask.user_id == user_id)

        active_tasks_query = select(func.count()).select_from(
            RecruitmentTask.__table__.where(
                and_(*task_filters, RecruitmentTask.status.in_(["not-started", "in-progress"]))
            )
        )
        active_tasks = await db.scalar(active_tasks_query)

        # 开放职位数
        job_filters = [Job.tenant_id == tenant_id]
        if user_id:
            job_filters.append(Job.user_id == user_id)

        open_jobs_query = select(func.count()).select_from(
            Job.__table__.where(and_(*job_filters, Job.status == "open"))
        )
        open_jobs = await db.scalar(open_jobs_query)

        return {
            "pendingResumes": pending_resumes or 0,
            "upcomingInterviews": upcoming_interviews or 0,
            "activeTasks": active_tasks or 0,
            "openJobs": open_jobs or 0
        }

    async def get_job_stats(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """获取职位统计数据"""
        base_filters = [Job.tenant_id == tenant_id]
        if user_id:
            base_filters.append(Job.user_id == user_id)

        # 总职位数
        total_jobs_query = select(func.count()).select_from(Job.__table__.where(and_(*base_filters)))
        total_jobs = await db.scalar(total_jobs_query)

        # 活跃职位数
        active_jobs_query = select(func.count()).select_from(
            Job.__table__.where(and_(*base_filters, Job.status == "open"))
        )
        active_jobs = await db.scalar(active_jobs_query)

        # 总申请人数（通过简历表关联）
        resumes_filters = [Resume.tenant_id == tenant_id]
        if user_id:
            resumes_filters.append(Resume.user_id == user_id)

        total_applicants_query = select(func.count()).select_from(Resume.__table__.where(and_(*resumes_filters)))
        total_applicants = await db.scalar(total_applicants_query)

        # 草稿职位数
        draft_jobs_query = select(func.count()).select_from(
            Job.__table__.where(and_(*base_filters, Job.status == "draft"))
        )
        draft_jobs = await db.scalar(draft_jobs_query)

        return {
            "totalJobs": total_jobs or 0,
            "activeJobs": active_jobs or 0,
            "totalApplicants": total_applicants or 0,
            "draftJobs": draft_jobs or 0
        }

    async def get_resume_stats(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """获取简历统计数据"""
        base_filters = [Resume.tenant_id == tenant_id]
        if user_id:
            base_filters.append(Resume.user_id == user_id)

        # 总数
        total_query = select(func.count()).select_from(Resume.__table__.where(and_(*base_filters)))
        total = await db.scalar(total_query)

        # 各状态统计
        status_stats = {}
        statuses = ["pending", "reviewing", "interview", "offered", "rejected"]

        for status in statuses:
            status_query = select(func.count()).select_from(
                Resume.__table__.where(and_(*base_filters, Resume.status == status))
            )
            count = await db.scalar(status_query)
            status_stats[status] = count or 0

        return {
            "total": total or 0,
            **status_stats
        }

    async def get_channel_stats(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """获取渠道统计数据"""
        base_filters = [Channel.tenant_id == tenant_id]
        if user_id:
            base_filters.append(Channel.user_id == user_id)

        # 总渠道数
        total_channels_query = select(func.count()).select_from(Channel.__table__.where(and_(*base_filters)))
        total_channels = await db.scalar(total_channels_query)

        # 活跃渠道数
        active_channels_query = select(func.count()).select_from(
            Channel.__table__.where(and_(*base_filters, Channel.status == "active"))
        )
        active_channels = await db.scalar(active_channels_query)

        # 总申请人数（通过简历表统计）
        resumes_filters = [Resume.tenant_id == tenant_id]
        if user_id:
            resumes_filters.append(Resume.user_id == user_id)

        total_applicants_query = select(func.count()).select_from(Resume.__table__.where(and_(*resumes_filters)))
        total_applicants = await db.scalar(total_applicants_query)

        # 平均转化率（申请到面试）
        interview_filters = [Interview.tenant_id == tenant_id]
        if user_id:
            interview_filters.append(Interview.user_id == user_id)

        total_interviews_query = select(func.count()).select_from(Interview.__table__.where(and_(*interview_filters)))
        total_interviews = await db.scalar(total_interviews_query)

        average_conversion = (total_interviews / total_applicants) if total_applicants and total_applicants > 0 else 0

        return {
            "totalChannels": total_channels or 0,
            "activeChannels": active_channels or 0,
            "totalApplicants": total_applicants or 0,
            "averageConversion": round(average_conversion, 3)
        }

    async def get_funnel_stats(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取招聘漏斗数据"""
        base_filters = [Resume.tenant_id == tenant_id]
        if user_id:
            base_filters.append(Resume.user_id == user_id)

        # 如果没有提供日期范围，使用最近30天
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # 总简历数
        total_resumes_query = select(func.count()).select_from(
            Resume.__table__.where(
                and_(*base_filters, Resume.submitted_at >= start_date, Resume.submitted_at <= end_date)
            )
        )
        total_resumes = await db.scalar(total_resumes_query)

        # 已安排面试数
        interview_filters = [Interview.tenant_id == tenant_id]
        if user_id:
            interview_filters.append(Interview.user_id == user_id)

        interview_scheduled_query = select(func.count()).select_from(
            Interview.__table__.where(
                and_(*interview_filters, Interview.created_at >= start_date, Interview.created_at <= end_date)
            )
        )
        interview_scheduled = await db.scalar(interview_scheduled_query)

        # 发出offer数（通过更新状态为offered的简历统计）
        offers_sent_query = select(func.count()).select_from(
            Resume.__table__.where(
                and_(*base_filters, Resume.status == "offered", Resume.updated_at >= start_date, Resume.updated_at <= end_date)
            )
        )
        offers_sent = await db.scalar(offers_sent_query)

        # 接受offer数（通过更新状态为interview但后来变成offered的简历统计）
        offers_accepted_query = select(func.count()).select_from(
            Resume.__table__.where(
                and_(*base_filters, Resume.status == "offered", Resume.updated_at >= start_date, Resume.updated_at <= end_date)
            )
        )
        offers_accepted = await db.scalar(offers_accepted_query)

        # 计算转化率
        resume_to_interview = (interview_scheduled / total_resumes) if total_resumes and total_resumes > 0 else 0
        interview_to_offer = (offers_sent / interview_scheduled) if interview_scheduled and interview_scheduled > 0 else 0
        offer_to_accept = (offers_accepted / offers_sent) if offers_sent and offers_sent > 0 else 0

        return {
            "totalResumes": total_resumes or 0,
            "interviewScheduled": interview_scheduled or 0,
            "offersSent": offers_sent or 0,
            "offersAccepted": offers_accepted or 0,
            "conversionRates": {
                "resumeToInterview": round(resume_to_interview, 3),
                "interviewToOffer": round(interview_to_offer, 3),
                "offerToAccept": round(offer_to_accept, 3)
            }
        }