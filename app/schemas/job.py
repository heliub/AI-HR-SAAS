"""
Job schemas
"""
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.base import BaseSchema, TimestampSchema, IDSchema


class JobBase(BaseModel):
    """职位基础Schema"""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    requirements: Optional[dict] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    employment_type: Optional[str] = None


class JobCreate(JobBase):
    """创建职位"""
    pass


class JobUpdate(BaseModel):
    """更新职位"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    requirements: Optional[dict] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    employment_type: Optional[str] = None
    status: Optional[str] = None


class JobResponse(JobBase, IDSchema, TimestampSchema):
    """职位响应"""
    tenant_id: int
    created_by: int
    status: str
    published_platforms: Optional[dict] = None
    closed_at: Optional[str] = None


class JobListResponse(BaseModel):
    """职位列表响应"""
    jobs: list[JobResponse]
    total: int

