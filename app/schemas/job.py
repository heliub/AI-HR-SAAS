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
    company: Optional[str] = Field(None, max_length=200, description="公司名称")
    location: str = Field(..., min_length=1, max_length=100)
    type: str
    workplaceType: Optional[str] = Field(None, alias="workplace_type", description="工作场所类型: On-site/Hybrid/Remote")
    minSalary: Optional[int] = Field(None, alias="min_salary", description="最低薪资（分）")
    maxSalary: Optional[int] = Field(None, alias="max_salary", description="最高薪资（分）")
    payType: Optional[str] = Field(None, alias="pay_type", description="薪资类型: Hourly/Monthly/Annual/Annual plus commission")
    payCurrency: Optional[str] = Field(None, alias="pay_currency", description="薪资货币: AUD/HKD/IDR/MYR/NZD/PHP/SGD/THB/USD")
    payShownOnAd: Optional[bool] = Field(None, alias="pay_shown_on_ad", description="是否在广告中显示薪资")
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    education: Optional[str] = None
    preferredSchools: Optional[List[str]] = Field(None, alias="preferred_schools")
    category: Optional[str] = Field(None, max_length=100, description="职位类别，如: IT-技术类, 销售-营销类, 财务-会计类")
    recruitmentInvitation: Optional[str] = Field(None, alias="recruitment_invitation")


class JobCreate(JobBase):
    """创建职位"""
    status: str = "draft"
    publishedChannels: Optional[List[UUID]] = Field(None, alias="published_channels")


class JobUpdate(BaseModel):
    """更新职位"""
    model_config = ConfigDict(populate_by_name=True)

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    company: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = None
    type: Optional[str] = None
    workplaceType: Optional[str] = Field(None, alias="workplace_type")
    minSalary: Optional[int] = Field(None, alias="min_salary")
    maxSalary: Optional[int] = Field(None, alias="max_salary")
    salary: Optional[str] = None  # 兼容字符串格式薪资，如 "30K-50K"
    payType: Optional[str] = Field(None, alias="pay_type")
    payCurrency: Optional[str] = Field(None, alias="pay_currency")
    payShownOnAd: Optional[bool] = Field(None, alias="pay_shown_on_ad")
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    education: Optional[str] = None
    preferredSchools: Optional[List[str]] = Field(None, alias="preferred_schools")
    category: Optional[str] = None
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

    company: Optional[str] = None
    location: str
    workplaceType: str = Field(alias="workplace_type")
    minSalary: int = Field(alias="min_salary")
    maxSalary: int = Field(alias="max_salary")
    payType: str = Field(alias="pay_type")
    payCurrency: str = Field(alias="pay_currency")
    payShownOnAd: bool = Field(alias="pay_shown_on_ad")
    description: str
    category: str
    recruitmentInvitation: str = Field(alias="recruitment_invitation")
    education: str

