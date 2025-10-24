"""
Resume schemas
"""
from typing import Optional
from pydantic import BaseModel
from app.schemas.base import BaseSchema, TimestampSchema, IDSchema


class ResumeBase(BaseModel):
    """简历基础Schema"""
    file_name: str
    file_type: str
    source: Optional[str] = None


class ResumeCreate(ResumeBase):
    """创建简历"""
    candidate_id: int
    job_id: Optional[int] = None
    file_key: str
    file_size: int


class ResumeUpdate(BaseModel):
    """更新简历"""
    structured_data: Optional[dict] = None
    parse_status: Optional[str] = None


class ResumeResponse(ResumeBase, IDSchema, TimestampSchema):
    """简历响应"""
    tenant_id: int
    candidate_id: int
    job_id: Optional[int] = None
    file_key: str
    file_size: int
    structured_data: Optional[dict] = None
    parse_status: str


class ResumeUploadResponse(BaseModel):
    """简历上传响应"""
    resume_id: int
    file_key: str
    parse_task_id: Optional[str] = None

