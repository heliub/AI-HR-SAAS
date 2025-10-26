"""
Interview endpoints
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.interview import (
    InterviewCreate, InterviewUpdate, InterviewCancelRequest, InterviewResponse
)
from app.schemas.base import APIResponse, PaginatedResponse
from app.models.user import User

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_interviews(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    candidateId: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取面试列表"""
    # TODO: 实现面试列表查询
    return APIResponse(
        code=200,
        message="成功",
        data={"list": [], "total": 0, "page": page, "pageSize": pageSize}
    )


@router.post("", response_model=APIResponse)
async def create_interview(
    interview_data: InterviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建面试"""
    # TODO: 实现面试创建
    return APIResponse(
        code=200,
        message="面试创建成功"
    )


@router.put("/{interview_id}", response_model=APIResponse)
async def update_interview(
    interview_id: UUID,
    interview_data: InterviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新面试"""
    # TODO: 实现面试更新
    return APIResponse(
        code=200,
        message="面试更新成功"
    )


@router.patch("/{interview_id}/cancel", response_model=APIResponse)
async def cancel_interview(
    interview_id: UUID,
    cancel_data: InterviewCancelRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消面试"""
    # TODO: 实现面试取消
    return APIResponse(
        code=200,
        message="面试已取消"
    )

