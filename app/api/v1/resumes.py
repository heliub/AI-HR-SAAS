"""
Resume endpoints
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.resume import (
    ResumeCreate, ResumeUpdate, ResumeStatusUpdate,
    ResumeResponse, AIMatchRequest, SendEmailRequest
)
from app.schemas.base import APIResponse, PaginatedResponse
from app.services.resume_service import ResumeService
from app.models.user import User

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_resumes(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    jobId: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取简历列表"""
    resume_service = ResumeService()
    
    resumes, total = await resume_service.get_resumes(
        db=db,
        tenant_id=current_user.tenant_id,
        page=page,
        page_size=pageSize,
        search=search,
        status=status,
        job_id=jobId
    )
    
    resume_responses = [ResumeResponse.model_validate(resume) for resume in resumes]
    
    paginated_data = PaginatedResponse(
        total=total,
        page=page,
        pageSize=pageSize,
        list=resume_responses
    )
    
    return APIResponse(
        code=200,
        message="成功",
        data=paginated_data.model_dump()
    )


@router.get("/{resume_id}", response_model=APIResponse)
async def get_resume(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取简历详情"""
    resume_service = ResumeService()
    
    resume = await resume_service.get(db, resume_id)
    
    if not resume or resume.tenant_id != current_user.tenant_id:
        return APIResponse(
            code=404,
            message="简历不存在"
        )
    
    resume_response = ResumeResponse.model_validate(resume)
    
    return APIResponse(
        code=200,
        message="成功",
        data=resume_response.model_dump()
    )


@router.patch("/{resume_id}/status", response_model=APIResponse)
async def update_resume_status(
    resume_id: UUID,
    status_data: ResumeStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新简历状态"""
    resume_service = ResumeService()
    
    resume = await resume_service.get(db, resume_id)
    if not resume or resume.tenant_id != current_user.tenant_id:
        return APIResponse(
            code=404,
            message="简历不存在"
        )
    
    await resume_service.update_resume(
        db=db,
        resume_id=resume_id,
        status=status_data.status
    )
    
    return APIResponse(
        code=200,
        message="状态更新成功"
    )


@router.post("/{resume_id}/ai-match", response_model=APIResponse)
async def ai_match_resume(
    resume_id: UUID,
    match_data: AIMatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI匹配分析"""
    resume_service = ResumeService()
    
    resume = await resume_service.get(db, resume_id)
    if not resume or resume.tenant_id != current_user.tenant_id:
        return APIResponse(
            code=404,
            message="简历不存在"
        )
    
    # TODO: 实现AI匹配逻辑
    # 这里返回模拟数据
    match_result = {
        "isMatch": True,
        "score": 92,
        "reason": "候选人具备丰富的前端开发经验...",
        "strengths": ["6年前端开发经验", "熟练掌握React/TypeScript"],
        "weaknesses": ["缺少移动端开发经验"],
        "recommendation": "强烈推荐面试"
    }
    
    return APIResponse(
        code=200,
        message="分析完成",
        data=match_result
    )


@router.post("/{resume_id}/send-email", response_model=APIResponse)
async def send_email_to_candidate(
    resume_id: UUID,
    email_data: SendEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送邮件"""
    resume_service = ResumeService()
    
    resume = await resume_service.get(db, resume_id)
    if not resume or resume.tenant_id != current_user.tenant_id:
        return APIResponse(
            code=404,
            message="简历不存在"
        )
    
    # TODO: 实现邮件发送逻辑
    
    return APIResponse(
        code=200,
        message="邮件发送成功"
    )


@router.get("/{resume_id}/download", response_model=APIResponse)
async def download_resume(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载简历"""
    resume_service = ResumeService()
    
    resume = await resume_service.get(db, resume_id)
    if not resume or resume.tenant_id != current_user.tenant_id:
        return APIResponse(
            code=404,
            message="简历不存在"
        )
    
    # TODO: 实现文件下载逻辑
    
    return APIResponse(
        code=200,
        message="成功",
        data={"resumeUrl": resume.resume_url}
    )

