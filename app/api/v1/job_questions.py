"""
Job Question endpoints
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.job_question import (
    JobQuestionCreate, JobQuestionUpdate, JobQuestionResponse,
    JobQuestionReorderRequest
)
from app.schemas.base import APIResponse, PaginatedResponse
from app.services.job_question_service import JobQuestionService
from app.services.job_service import JobService
from app.models.user import User
from app.models.job import Job
from app.models.job_question import JobQuestion as JobQuestionModel

router = APIRouter()


@router.get("/jobs/{job_id}/questions", response_model=APIResponse)
async def get_job_questions(
    job_id: UUID,
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取职位问题列表"""
    job_question_service = JobQuestionService(db)
    
    # 验证职位是否存在
    job_service = JobService(db)
    job = await job_service.get_by_id(Job, job_id, current_user.tenant_id)
    if not job:
        raise HTTPException(status_code=404, detail="职位不存在")
    
    # 判断是否为管理员
    is_admin = current_user.role == "admin"
    
    # 获取问题列表
    questions = await job_question_service.get_questions_by_job(
        job_id=job_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        is_admin=is_admin
    )
    
    # 计算总数
    total = len(questions)
    
    # 分页处理
    skip = (page - 1) * pageSize
    paginated_questions = questions[skip:skip + pageSize]
    
    # 转换为响应模型
    question_responses = []
    for question in paginated_questions:
        question_response = JobQuestionResponse.model_validate(question.__dict__)
        question_responses.append(question_response)
    
    paginated_data = PaginatedResponse(
        total=total,
        page=page,
        pageSize=pageSize,
        list=question_responses
    )
    
    return APIResponse(
        code=200,
        message="成功",
        data=paginated_data.model_dump()
    )


@router.get("/questions/{question_id}", response_model=APIResponse)
async def get_job_question(
    question_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取职位问题详情"""
    job_question_service = JobQuestionService(db)
    
    # 判断是否为管理员
    is_admin = current_user.role == "admin"
    
    # 获取问题详情
    question = await job_question_service.get_by_id(
        model=JobQuestionModel,
        record_id=question_id,
        tenant_id=current_user.tenant_id
    )
    
    if not question:
        raise HTTPException(status_code=404, detail="问题不存在")
    
    # 检查权限
    if not is_admin and question.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限访问此问题")
    
    # 转换为响应模型
    question_response = JobQuestionResponse.model_validate(question.__dict__)
    
    return APIResponse(
        code=200,
        message="成功",
        data=question_response.model_dump()
    )


@router.post("/jobs/{job_id}/questions", response_model=APIResponse)
async def create_job_question(
    job_id: UUID,
    question_data: JobQuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建职位问题"""
    job_question_service = JobQuestionService(db)
    
    # 验证职位是否存在
    job_service = JobService(db)
    job = await job_service.get_by_id(Job, job_id, current_user.tenant_id)
    if not job:
        raise HTTPException(status_code=404, detail="职位不存在")
    
    # 创建问题
    question = await job_question_service.create_question(
        job_id=job_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        question_data=question_data.model_dump(by_alias=True)
    )
    
    # 转换为响应模型
    question_response = JobQuestionResponse.model_validate(question.__dict__)
    
    return APIResponse(
        code=200,
        message="创建成功",
        data=question_response.model_dump()
    )


@router.put("/questions/{question_id}", response_model=APIResponse)
async def update_job_question(
    question_id: UUID,
    question_data: JobQuestionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新职位问题"""
    job_question_service = JobQuestionService(db)
    
    # 判断是否为管理员
    is_admin = current_user.role == "admin"
    
    # 更新问题
    question = await job_question_service.update_question(
        question_id=question_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        is_admin=is_admin,
        question_data=question_data.model_dump(by_alias=True, exclude_unset=True)
    )
    
    if not question:
        raise HTTPException(status_code=404, detail="问题不存在")
    
    # 转换为响应模型
    question_response = JobQuestionResponse.model_validate(question.__dict__)
    
    return APIResponse(
        code=200,
        message="更新成功",
        data=question_response.model_dump()
    )


@router.delete("/questions/{question_id}", response_model=APIResponse)
async def delete_job_question(
    question_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除职位问题"""
    job_question_service = JobQuestionService(db)
    
    # 判断是否为管理员
    is_admin = current_user.role == "admin"
    
    # 删除问题
    success = await job_question_service.delete_question(
        question_id=question_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        is_admin=is_admin
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="问题不存在")
    
    return APIResponse(
        code=200,
        message="删除成功",
        data=None
    )


@router.post("/jobs/{job_id}/questions/reorder", response_model=APIResponse)
async def reorder_job_questions(
    job_id: UUID,
    reorder_data: JobQuestionReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重新排序职位问题"""
    job_question_service = JobQuestionService(db)
    
    # 验证职位是否存在
    job_service = JobService(db)
    job = await job_service.get_by_id(Job, job_id, current_user.tenant_id)
    if not job:
        raise HTTPException(status_code=404, detail="职位不存在")
    
    # 判断是否为管理员
    is_admin = current_user.role == "admin"
    
    # 重新排序问题
    success = await job_question_service.reorder_questions(
        job_id=job_id,
        tenant_id=current_user.tenant_id,
        question_orders=reorder_data.model_dump(by_alias=True)["questions"],
        user_id=current_user.id,
        is_admin=is_admin
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="排序失败")
    
    return APIResponse(
        code=200,
        message="排序成功",
        data=None
    )
