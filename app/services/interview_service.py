"""
Interview service
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import Interview
from app.services.base import BaseService
from app.core.exceptions import NotFoundException


class InterviewService(BaseService[Interview]):
    """面试服务"""

    def __init__(self):
        super().__init__(Interview)

    async def get_interviews(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        *,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        candidate_id: Optional[UUID] = None
    ) -> tuple[List[Interview], int]:
        """获取面试列表"""
        query = select(Interview).where(Interview.tenant_id == tenant_id)

        # 用户级数据隔离
        if user_id:
            query = query.where(Interview.user_id == user_id)

        # 状态筛选
        if status:
            query = query.where(Interview.status == status)

        # 候选人筛选
        if candidate_id:
            query = query.where(Interview.candidate_id == candidate_id)

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)

        # 按面试日期和时间排序
        query = query.order_by(
            Interview.interview_date.asc(),
            Interview.interview_time.asc()
        )
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        interviews = result.scalars().all()

        return list(interviews), total or 0

    async def create_interview(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        user_id: UUID,
        **interview_data
    ) -> Interview:
        """创建面试"""
        interview_data.update({
            "tenant_id": tenant_id,
            "user_id": user_id,
            "status": "scheduled"
        })

        interview = Interview(**interview_data)
        db.add(interview)
        await db.commit()
        await db.refresh(interview)

        return interview

    async def update_interview(
        self,
        db: AsyncSession,
        interview_id: UUID,
        **update_data
    ) -> Interview:
        """更新面试"""
        interview = await self.get(db, interview_id)
        if not interview:
            raise NotFoundException("Interview not found")

        for key, value in update_data.items():
            if value is not None:
                setattr(interview, key, value)

        await db.commit()
        await db.refresh(interview)

        return interview

    async def cancel_interview(
        self,
        db: AsyncSession,
        interview_id: UUID,
        cancellation_reason: Optional[str] = None
    ) -> Interview:
        """取消面试"""
        interview = await self.get(db, interview_id)
        if not interview:
            raise NotFoundException("Interview not found")

        interview.status = "cancelled"
        interview.cancelled_at = datetime.utcnow()
        if cancellation_reason:
            interview.cancellation_reason = cancellation_reason

        await db.commit()
        await db.refresh(interview)

        return interview

    async def get_upcoming_interviews(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        limit: int = 5
    ) -> List[Interview]:
        """获取即将到来的面试"""
        now = datetime.utcnow().date()

        query = select(Interview).where(
            and_(
                Interview.tenant_id == tenant_id,
                Interview.interview_date >= now,
                Interview.status == "scheduled"
            )
        )

        # 用户级数据隔离
        if user_id:
            query = query.where(Interview.user_id == user_id)

        query = query.order_by(
            Interview.interview_date.asc(),
            Interview.interview_time.asc()
        ).limit(limit)

        result = await db.execute(query)
        interviews = result.scalars().all()

        return list(interviews)