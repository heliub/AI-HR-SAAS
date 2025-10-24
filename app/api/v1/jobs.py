"""
Job endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.job import JobCreate, JobResponse, JobListResponse
from app.services.job_service import JobService
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=JobResponse)
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
        **job_data.model_dump()
    )
    
    return JobResponse.model_validate(job)


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取职位列表"""
    job_service = JobService()
    
    jobs = await job_service.get_open_jobs(
        db=db,
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=limit
    )
    
    return JobListResponse(
        jobs=[JobResponse.model_validate(j) for j in jobs],
        total=len(jobs)
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取职位详情"""
    job_service = JobService()
    
    job = await job_service.get_by_id(
        db=db,
        id=job_id,
        tenant_id=current_user.tenant_id
    )
    
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse.model_validate(job)

