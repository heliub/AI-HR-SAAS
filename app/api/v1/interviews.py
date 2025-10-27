"""
Interview endpoints
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.interview import (
    InterviewCreate, InterviewUpdate, InterviewCancelRequest, InterviewResponse
)
from app.schemas.base import APIResponse, PaginatedResponse
from app.services.interview_service import InterviewService
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
    interview_service = InterviewService()

    interviews, total = await interview_service.get_interviews(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        page=page,
        page_size=pageSize,
        status=status,
        candidate_id=candidateId
    )

    interview_responses = [InterviewResponse.model_validate({
        "id": str(interview.id),
        "tenantId": str(interview.tenant_id),
        "userId": str(interview.user_id) if interview.user_id else None,
        "candidateId": interview.candidate_id,
        "candidateName": interview.candidate_name,
        "position": interview.position,
        "date": interview.interview_date,
        "time": interview.interview_time,
        "interviewer": interview.interviewer,
        "interviewerTitle": interview.interviewer_title,
        "type": interview.type,
        "status": interview.status,
        "location": interview.location,
        "meetingLink": interview.meeting_link,
        "notes": interview.notes,
        "createdAt": interview.created_at.isoformat() if interview.created_at else None,
        "updatedAt": interview.updated_at.isoformat() if interview.updated_at else None
    }) for interview in interviews]

    paginated_data = PaginatedResponse(
        total=total,
        page=page,
        pageSize=pageSize,
        list=interview_responses
    )

    return APIResponse(
        code=200,
        message="成功",
        data=paginated_data.model_dump()
    )


@router.post("", response_model=APIResponse)
async def create_interview(
    interview_data: InterviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建面试"""
    interview_service = InterviewService()

    interview = await interview_service.create_interview(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        **interview_data.model_dump(exclude_unset=True)
    )

    interview_response = InterviewResponse.model_validate({
        "id": str(interview.id),
        "tenantId": str(interview.tenant_id),
        "userId": str(interview.user_id) if interview.user_id else None,
        "candidateId": interview.candidate_id,
        "candidateName": interview.candidate_name,
        "position": interview.position,
        "date": interview.interview_date,
        "time": interview.interview_time,
        "interviewer": interview.interviewer,
        "interviewerTitle": interview.interviewer_title,
        "type": interview.type,
        "status": interview.status,
        "location": interview.location,
        "meetingLink": interview.meeting_link,
        "notes": interview.notes,
        "createdAt": interview.created_at.isoformat() if interview.created_at else None,
        "updatedAt": interview.updated_at.isoformat() if interview.updated_at else None
    })

    return APIResponse(
        code=200,
        message="面试创建成功",
        data=interview_response.model_dump()
    )


@router.put("/{interview_id}", response_model=APIResponse)
async def update_interview(
    interview_id: UUID,
    interview_data: InterviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新面试"""
    interview_service = InterviewService()

    # 检查面试是否存在
    interview = await interview_service.get(db, interview_id)
    if not interview or interview.tenant_id != current_user.tenant_id or interview.user_id != current_user.id:
        return APIResponse(
            code=404,
            message="面试不存在"
        )

    interview = await interview_service.update_interview(
        db=db,
        interview_id=interview_id,
        **interview_data.model_dump(exclude_unset=True)
    )

    interview_response = InterviewResponse.model_validate({
        "id": str(interview.id),
        "tenantId": str(interview.tenant_id),
        "userId": str(interview.user_id) if interview.user_id else None,
        "candidateId": interview.candidate_id,
        "candidateName": interview.candidate_name,
        "position": interview.position,
        "date": interview.interview_date,
        "time": interview.interview_time,
        "interviewer": interview.interviewer,
        "interviewerTitle": interview.interviewer_title,
        "type": interview.type,
        "status": interview.status,
        "location": interview.location,
        "meetingLink": interview.meeting_link,
        "notes": interview.notes,
        "createdAt": interview.created_at.isoformat() if interview.created_at else None,
        "updatedAt": interview.updated_at.isoformat() if interview.updated_at else None
    })

    return APIResponse(
        code=200,
        message="面试更新成功",
        data=interview_response.model_dump()
    )


@router.patch("/{interview_id}/cancel", response_model=APIResponse)
async def cancel_interview(
    interview_id: UUID,
    cancel_data: InterviewCancelRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消面试"""
    interview_service = InterviewService()

    # 检查面试是否存在
    interview = await interview_service.get(db, interview_id)
    if not interview or interview.tenant_id != current_user.tenant_id or interview.user_id != current_user.id:
        return APIResponse(
            code=404,
            message="面试不存在"
        )

    await interview_service.cancel_interview(
        db=db,
        interview_id=interview_id,
        cancellation_reason=cancel_data.reason
    )

    return APIResponse(
        code=200,
        message="面试已取消"
    )

