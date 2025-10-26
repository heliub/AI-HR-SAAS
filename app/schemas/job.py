"""
Job schemas
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.base import BaseSchema, TimestampSchema, IDSchema


class JobBase(BaseModel):
    """职位基础Schema"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    title: str = Field(..., min_length=1, max_length=200)
    department: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=100)
    type: str
    min_salary: Optional[int] = Field(None, validation_alias="minSalary", serialization_alias="minSalary", description="最低薪资（元/月）")
    max_salary: Optional[int] = Field(None, validation_alias="maxSalary", serialization_alias="maxSalary", description="最高薪资（元/月）")
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    min_age: Optional[int] = Field(None, validation_alias="minAge", serialization_alias="minAge", description="最低年龄")
    max_age: Optional[int] = Field(None, validation_alias="maxAge", serialization_alias="maxAge", description="最高年龄")
    gender: Optional[str] = None
    education: Optional[str] = None
    preferred_schools: Optional[List[str]] = Field(None, validation_alias="preferredSchools", serialization_alias="preferredSchools")
    job_level: Optional[str] = Field(None, validation_alias="jobLevel", serialization_alias="jobLevel")
    recruitment_invitation: Optional[str] = Field(None, validation_alias="recruitmentInvitation", serialization_alias="recruitmentInvitation")


class JobCreate(JobBase):
    """创建职位"""
    status: str = "draft"
    publishedChannels: Optional[List[UUID]] = None


class JobUpdate(BaseModel):
    """更新职位"""
    model_config = ConfigDict(populate_by_name=True)
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    department: Optional[str] = None
    location: Optional[str] = None
    type: Optional[str] = None
    min_salary: Optional[int] = Field(None, validation_alias="minSalary", serialization_alias="minSalary")
    max_salary: Optional[int] = Field(None, validation_alias="maxSalary", serialization_alias="maxSalary")
    salary: Optional[str] = None  # 兼容字符串格式薪资，如 "30K-50K"
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    min_age: Optional[int] = Field(None, validation_alias="minAge", serialization_alias="minAge")
    max_age: Optional[int] = Field(None, validation_alias="maxAge", serialization_alias="maxAge")
    gender: Optional[str] = None
    education: Optional[str] = None
    preferred_schools: Optional[List[str]] = Field(None, validation_alias="preferredSchools", serialization_alias="preferredSchools")
    job_level: Optional[str] = Field(None, validation_alias="jobLevel", serialization_alias="jobLevel")
    recruitment_invitation: Optional[str] = Field(None, validation_alias="recruitmentInvitation", serialization_alias="recruitmentInvitation")
    publishedChannels: Optional[List[UUID]] = None


class JobStatusUpdate(BaseModel):
    """职位状态更新"""
    status: str


class JobResponse(JobBase, IDSchema, TimestampSchema):
    """职位响应"""
    status: str
    salary: Optional[str] = None  # 兼容字符串格式薪资，如 "30K-50K"
    applicants: int = 0
    publishedChannels: Optional[List[UUID]] = None
    publishedAt: Optional[datetime] = None


class JobAIGenerateRequest(BaseModel):
    """AI生成职位描述请求"""
    title: str
    job_level: Optional[str] = Field(None, validation_alias="jobLevel")


class JobAIGenerateResponse(BaseModel):
    """AI生成职位描述响应"""
    model_config = ConfigDict(populate_by_name=True)
    
    department: str
    location: str
    min_salary: int = Field(..., serialization_alias="minSalary")
    max_salary: int = Field(..., serialization_alias="maxSalary")
    description: str
    recruitment_invitation: str = Field(..., serialization_alias="recruitmentInvitation")
    education: str
    min_age: int = Field(..., serialization_alias="minAge")
    max_age: int = Field(..., serialization_alias="maxAge")

