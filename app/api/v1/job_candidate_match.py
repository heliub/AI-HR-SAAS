"""
人岗匹配API端点
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import get_current_user, get_db
from app.api.responses import create_success_response, handle_service_error
from app.models.user import User
from app.services.job_candidate_match_service import JobCandidateMatchService
from app.schemas.job_candidate_match import MatchRequest, MatchResponse
from app.schemas.base import APIResponse

router = APIRouter()


@router.post("/match", response_model=APIResponse)
async def match_job_candidate(
    request: MatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    执行人岗匹配
    
    Args:
        request: 匹配请求
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        匹配结果
    """
    match_service = JobCandidateMatchService(db)
    
    try:
        result = await match_service.match_job_candidate(
            job_id=request.jobId,
            resume_id=request.resumeId,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id
        )
        
        if not result:
            return handle_service_error(Exception("匹配失败，请稍后重试"), "人岗匹配")
        match_response = MatchResponse.model_validate(result, from_attributes=True)
        return create_success_response(
            message="人岗匹配成功",
            data=match_response.model_dump()
        )
        
    except Exception as e:
        return handle_service_error(e, "人岗匹配")
