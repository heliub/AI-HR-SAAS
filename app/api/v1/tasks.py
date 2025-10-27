"""
Recruitment Task endpoints
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.task import (
    RecruitmentTaskCreate, RecruitmentTaskStatusUpdate,
    RecruitmentTaskProgressUpdate, RecruitmentTaskResponse
)
from app.schemas.base import APIResponse, PaginatedResponse
from app.services.task_service import TaskService
from app.models.user import User

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_tasks(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务列表"""
    task_service = TaskService()

    tasks, total = await task_service.get_tasks(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        page=page,
        page_size=pageSize,
        status=status
    )

    task_responses = [RecruitmentTaskResponse.model_validate(task) for task in tasks]

    paginated_data = PaginatedResponse(
        total=total,
        page=page,
        pageSize=pageSize,
        list=task_responses
    )

    return APIResponse(
        code=200,
        message="成功",
        data=paginated_data.model_dump()
    )


@router.post("", response_model=APIResponse)
async def create_task(
    task_data: RecruitmentTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建任务"""
    task_service = TaskService()

    task = await task_service.create_task(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        job_id=task_data.jobId,
        job_title=task_data.jobTitle,
        total_channels=task_data.totalChannels,
        created_by=current_user.id
    )

    task_response = RecruitmentTaskResponse.model_validate(task)

    return APIResponse(
        code=200,
        message="任务创建成功",
        data=task_response.model_dump()
    )


@router.patch("/{task_id}/status", response_model=APIResponse)
async def update_task_status(
    task_id: UUID,
    status_data: RecruitmentTaskStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新任务状态"""
    task_service = TaskService()

    # 检查任务是否存在
    task = await task_service.get(db, task_id)
    if not task or task.tenant_id != current_user.tenant_id or task.user_id != current_user.id:
        return APIResponse(
            code=404,
            message="任务不存在"
        )

    await task_service.update_task_status(
        db=db,
        task_id=task_id,
        status=status_data.status
    )

    return APIResponse(
        code=200,
        message="状态更新成功"
    )


@router.patch("/{task_id}/progress", response_model=APIResponse)
async def update_task_progress(
    task_id: UUID,
    progress_data: RecruitmentTaskProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新任务进度"""
    task_service = TaskService()

    # 检查任务是否存在
    task = await task_service.get(db, task_id)
    if not task or task.tenant_id != current_user.tenant_id or task.user_id != current_user.id:
        return APIResponse(
            code=404,
            message="任务不存在"
        )

    await task_service.update_task_progress(
        db=db,
        task_id=task_id,
        **progress_data.model_dump(exclude_unset=True)
    )

    return APIResponse(
        code=200,
        message="进度更新成功"
    )

