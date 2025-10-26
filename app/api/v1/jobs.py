"""
Job endpoints
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.job import (
    JobCreate, JobUpdate, JobStatusUpdate, JobResponse,
    JobAIGenerateRequest, JobAIGenerateResponse
)
from app.schemas.base import APIResponse, PaginatedResponse
from app.services.job_service import JobService
from app.models.user import User

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_jobs(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    department: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取职位列表"""
    job_service = JobService()
    
    jobs, total = await job_service.get_jobs(
        db=db,
        tenant_id=current_user.tenant_id,
        page=page,
        page_size=pageSize,
        search=search,
        status=status,
        department=department
    )
    
    job_responses = [JobResponse.model_validate(job) for job in jobs]
    
    paginated_data = PaginatedResponse(
        total=total,
        page=page,
        pageSize=pageSize,
        list=job_responses
    )
    
    return APIResponse(
        code=200,
        message="成功",
        data=paginated_data.model_dump()
    )


@router.get("/{job_id}", response_model=APIResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取职位详情"""
    job_service = JobService()
    
    job = await job_service.get(db, job_id)
    
    if not job or job.tenant_id != current_user.tenant_id:
        return APIResponse(
            code=404,
            message="职位不存在"
        )
    
    job_response = JobResponse.model_validate(job)
    
    return APIResponse(
        code=200,
        message="成功",
        data=job_response.model_dump()
    )


@router.post("", response_model=APIResponse)
async def create_job(
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建职位"""
    job_service = JobService()
    
    job = await job_service.create_job(
        db=db,
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        **job_data.model_dump(exclude_unset=True)
    )
    
    job_response = JobResponse.model_validate(job)
    
    return APIResponse(
        code=200,
        message="职位创建成功",
        data=job_response.model_dump()
    )


@router.put("/{job_id}", response_model=APIResponse)
async def update_job(
    job_id: UUID,
    job_data: JobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新职位"""
    job_service = JobService()
    
    # 检查职位是否存在
    job = await job_service.get(db, job_id)
    if not job or job.tenant_id != current_user.tenant_id:
        return APIResponse(
            code=404,
            message="职位不存在"
        )
    
    job = await job_service.update_job(
        db=db,
        job_id=job_id,
        **job_data.model_dump(exclude_unset=True)
    )
    
    job_response = JobResponse.model_validate(job)
    
    return APIResponse(
        code=200,
        message="职位更新成功",
        data=job_response.model_dump()
    )


@router.delete("/{job_id}", response_model=APIResponse)
async def delete_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除职位"""
    job_service = JobService()
    
    # 检查职位是否存在
    job = await job_service.get(db, job_id)
    if not job or job.tenant_id != current_user.tenant_id:
        return APIResponse(
            code=404,
            message="职位不存在"
        )
    
    await job_service.delete(db, job_id)
    
    return APIResponse(
        code=200,
        message="职位删除成功"
    )


@router.patch("/{job_id}/status", response_model=APIResponse)
async def update_job_status(
    job_id: UUID,
    status_data: JobStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新职位状态"""
    job_service = JobService()
    
    # 检查职位是否存在
    job = await job_service.get(db, job_id)
    if not job or job.tenant_id != current_user.tenant_id:
        return APIResponse(
            code=404,
            message="职位不存在"
        )
    
    job = await job_service.update_job(
        db=db,
        job_id=job_id,
        status=status_data.status
    )
    
    return APIResponse(
        code=200,
        message="状态更新成功"
    )


@router.post("/{job_id}/duplicate", response_model=APIResponse)
async def duplicate_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """复制职位"""
    job_service = JobService()
    
    # 检查职位是否存在
    job = await job_service.get(db, job_id)
    if not job or job.tenant_id != current_user.tenant_id:
        return APIResponse(
            code=404,
            message="职位不存在"
        )
    
    new_job = await job_service.duplicate_job(
        db=db,
        job_id=job_id,
        created_by=current_user.id
    )
    
    job_response = JobResponse.model_validate(new_job)
    
    return APIResponse(
        code=200,
        message="职位复制成功",
        data=job_response.model_dump()
    )


@router.post("/ai-generate", response_model=APIResponse)
async def ai_generate_job(
    request_data: JobAIGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI生成职位描述"""
    # TODO: 实现AI生成逻辑
    # 这里返回模拟数据
    response_data = JobAIGenerateResponse(
        department="技术部",
        location="北京",
        min_salary=25000,
        max_salary=40000,
        description=f"负责公司核心产品的{request_data.title}工作...",
        recruitment_invitation=f"我们正在寻找有激情的{request_data.title}...",
        education="本科及以上",
        min_age=25,
        max_age=40
    )
    
    return APIResponse(
        code=200,
        message="生成成功",
        data=response_data.model_dump(by_alias=True)
    )
