"""
Job schemas
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from app.schemas.base import BaseSchema, TimestampSchema, IDSchema
from app.utils.datetime_formatter import format_datetime


class JobBase(BaseModel):
    """职位基础Schema"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    title: str = Field(..., min_length=1, max_length=200)
    department: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=100)
    type: str
    minSalary: Optional[int] = Field(None, alias="min_salary", description="最低薪资（元/月）")
    maxSalary: Optional[int] = Field(None, alias="max_salary", description="最高薪资（元/月）")
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    minAge: Optional[int] = Field(None, alias="min_age", description="最低年龄")
    maxAge: Optional[int] = Field(None, alias="max_age", description="最高年龄")
    gender: Optional[str] = None
    education: Optional[str] = None
    preferredSchools: Optional[List[str]] = Field(None, alias="preferred_schools")
    jobLevel: Optional[str] = Field(None, alias="job_level")
    recruitmentInvitation: Optional[str] = Field(None, alias="recruitment_invitation")


class JobCreate(JobBase):
    """创建职位"""
    status: str = "draft"
    publishedChannels: Optional[List[UUID]] = Field(None, alias="published_channels")


class JobUpdate(BaseModel):
    """更新职位"""
    model_config = ConfigDict(populate_by_name=True)

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    department: Optional[str] = None
    location: Optional[str] = None
    type: Optional[str] = None
    minSalary: Optional[int] = Field(None, alias="min_salary")
    maxSalary: Optional[int] = Field(None, alias="max_salary")
    salary: Optional[str] = None  # 兼容字符串格式薪资，如 "30K-50K"
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    minAge: Optional[int] = Field(None, alias="min_age")
    maxAge: Optional[int] = Field(None, alias="max_age")
    gender: Optional[str] = None
    education: Optional[str] = None
    preferredSchools: Optional[List[str]] = Field(None, alias="preferred_schools")
    jobLevel: Optional[str] = Field(None, alias="job_level")
    recruitmentInvitation: Optional[str] = Field(None, alias="recruitment_invitation")
    publishedChannels: Optional[List[UUID]] = Field(None, alias="published_channels")


class JobStatusUpdate(BaseModel):
    """职位状态更新"""
    status: str


class JobResponse(JobBase, IDSchema, TimestampSchema):
    """职位响应"""
    userId: Optional[UUID] = Field(alias="user_id")
    status: str
    salary: Optional[str] = None  # 兼容字符串格式薪资，如 "30K-50K"
    applicantsCount: int = Field(alias="applicants_count")
    publishedChannels: Optional[List[UUID]] = Field(default=[], alias="published_channels")
    publishedAt: Optional[datetime] = Field(None, alias="published_at")

    @field_serializer('publishedAt')
    def serialize_published_at(self, value: Optional[datetime]) -> Optional[str]:
        """格式化发布时间为可读格式"""
        return format_datetime(value)


class JobAIGenerateRequest(BaseModel):
    """AI生成职位描述请求"""
    title: str
    jobLevel: Optional[str] = Field(alias="job_level")


class JobAIGenerateResponse(BaseModel):
    """AI生成职位描述响应"""
    model_config = ConfigDict(populate_by_name=True)

    department: str
    location: str
    minSalary: int = Field(alias="min_salary")
    maxSalary: int = Field(alias="max_salary")
    description: str
    recruitmentInvitation: str = Field(alias="recruitment_invitation")
    education: str
    minAge: int = Field(alias="min_age")
    maxAge: int = Field(alias="max_age")

