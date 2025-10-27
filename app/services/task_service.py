"""
Task service
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recruitment_task import RecruitmentTask
from app.services.base import BaseService
from app.core.exceptions import NotFoundException


class TaskService(BaseService[RecruitmentTask]):
    """招聘任务服务"""

    def __init__(self):
        super().__init__(RecruitmentTask)

    async def get_tasks(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        *,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        is_admin: bool = False
    ) -> tuple[List[RecruitmentTask], int]:
        """获取任务列表"""
        query = select(RecruitmentTask).where(RecruitmentTask.tenant_id == tenant_id)

        # 用户级数据隔离 - 只有非管理员才过滤user_id
        if user_id and not is_admin:
            query = query.where(RecruitmentTask.user_id == user_id)

        # 状态筛选
        if status:
            query = query.where(RecruitmentTask.status == status)

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)

        # 按创建时间倒序
        query = query.order_by(RecruitmentTask.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        tasks = result.scalars().all()

        return list(tasks), total or 0

    async def create_task(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        user_id: UUID,
        job_id: UUID,
        job_title: str,
        total_channels: int = 0,
        **task_data
    ) -> RecruitmentTask:
        """创建任务"""
        task_data.update({
            "tenant_id": tenant_id,
            "user_id": user_id,
            "job_id": job_id,
            "job_title": job_title,
            "total_channels": total_channels,
            "status": "not-started",
            "created_by": user_id
        })

        task = RecruitmentTask(**task_data)
        db.add(task)
        await db.commit()
        await db.refresh(task)

        return task

    async def update_task_status(
        self,
        db: AsyncSession,
        task_id: UUID,
        status: str
    ) -> RecruitmentTask:
        """更新任务状态"""
        task = await self.get(db, task_id)
        if not task:
            raise NotFoundException("Task not found")

        task.status = status
        if status == "completed":
            from datetime import datetime
            task.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(task)

        return task

    async def update_task_progress(
        self,
        db: AsyncSession,
        task_id: UUID,
        **progress_data
    ) -> RecruitmentTask:
        """更新任务进度"""
        task = await self.get(db, task_id)
        if not task:
            raise NotFoundException("Task not found")

        # 更新进度字段
        for field, value in progress_data.items():
            if hasattr(task, field) and value is not None:
                setattr(task, field, value)

        await db.commit()
        await db.refresh(task)

        return task

    async def get_active_tasks(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: Optional[UUID] = None
    ) -> List[RecruitmentTask]:
        """获取活跃任务"""
        query = select(RecruitmentTask).where(
            RecruitmentTask.tenant_id == tenant_id,
            RecruitmentTask.status.in_(["not-started", "in-progress"])
        )

        # 用户级数据隔离
        if user_id:
            query = query.where(RecruitmentTask.user_id == user_id)

        query = query.order_by(RecruitmentTask.created_at.desc())

        result = await db.execute(query)
        tasks = result.scalars().all()

        return list(tasks)

    async def get_task_statistics(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: Optional[UUID] = None
    ) -> dict:
        """获取任务统计信息"""
        # 基础查询
        base_query = select(RecruitmentTask).where(RecruitmentTask.tenant_id == tenant_id)

        # 用户级数据隔离
        if user_id:
            base_query = base_query.where(RecruitmentTask.user_id == user_id)

        # 总任务数
        total_query = select(func.count()).select_from(base_query.subquery())
        total = await db.scalar(total_query)

        # 活跃任务数
        active_query = select(func.count()).select_from(
            base_query.where(
                RecruitmentTask.status.in_(["not-started", "in-progress"])
            ).subquery()
        )
        active = await db.scalar(active_query)

        # 已完成任务数
        completed_query = select(func.count()).select_from(
            base_query.where(RecruitmentTask.status == "completed").subquery()
        )
        completed = await db.scalar(completed_query)

        return {
            "totalTasks": total or 0,
            "activeTasks": active or 0,
            "completedTasks": completed or 0
        }