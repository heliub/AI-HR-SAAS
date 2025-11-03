"""
Resume schemas
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field, field_serializer
from app.schemas.base import BaseSchema, TimestampSchema, IDSchema
from app.schemas.interview import InterviewResponse, EmailLogResponse
from app.utils.datetime_formatter import format_datetime, format_date


class WorkExperienceBase(BaseModel):
    """工作经历基础Schema"""
    company: str
    position: str
    startDate: Optional[str] = Field(None, alias="start_date")
    endDate: Optional[str] = Field(None, alias="end_date")
    description: Optional[str] = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class ProjectExperienceBase(BaseModel):
    """项目经历基础Schema"""
    name: str = Field(alias="project_name")
    role: Optional[str] = None
    startDate: Optional[str] = Field(None, alias="start_date")
    endDate: Optional[str] = Field(None, alias="end_date")
    description: Optional[str] = None
    technologies: Optional[str] = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class EducationHistoryBase(BaseModel):
    """教育经历基础Schema"""
    school: str
    degree: Optional[str] = None
    major: Optional[str] = None
    startDate: Optional[str] = Field(None, alias="start_date")
    endDate: Optional[str] = Field(None, alias="end_date")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class JobPreferenceBase(BaseModel):
    """求职意向基础Schema"""
    expectedSalary: Optional[str] = Field(None, alias="expected_salary")
    preferredLocations: Optional[str] = Field(None, alias="preferred_locations")
    jobType: Optional[str] = Field(None, alias="job_type")
    availableDate: Optional[date] = Field(None, alias="available_date")

    @field_serializer('availableDate')
    def serialize_available_date(self, value: Optional[date]) -> Optional[str]:
        """格式化日期为可读格式"""
        if value is None:
            return None
        return value.strftime("%Y-%m-%d")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class AIMatchBase(BaseModel):
    """AI匹配基础Schema"""
    isMatch: bool = Field(alias="is_match")
    score: Optional[int] = Field(None, alias="match_score")
    reason: Optional[str] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    recommendation: Optional[str] = None
    status: Optional[str] = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class CandidateChatHistoryBase(BaseModel):
    """候选人聊天历史基础Schema"""
    sender: str
    message: str
    created_at: str  # 已经格式化过的字符串
    timestamp: Optional[str] = Field(None, alias="created_at")

    model_config = {
        "from_attributes": False,  # 因为现在传递的是字符串而不是模型实例
        "populate_by_name": True
    }


class ResumeBase(BaseModel):
    """简历基础Schema"""
    candidateName: str = Field(alias="candidate_name")
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    position: str
    jobId: Optional[UUID] = Field(alias="job_id")
    source: Optional[str] = None
    experienceYears: Optional[str] = Field(alias="experience_years")
    educationLevel: Optional[str] = Field(alias="education_level")
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    school: Optional[str] = None
    major: Optional[str] = None
    skills: Optional[str] = None
    isMatch: Optional[bool] = Field(None, alias="is_match")
    matchConclusion: Optional[str] = Field(None, alias="match_conclusion")


class ResumeCreate(ResumeBase):
    """创建简历"""
    jobId: Optional[UUID] = Field(None, alias="job_id")


class ResumeUpdate(BaseModel):
    """更新简历"""
    candidateName: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None


class ResumeStatusUpdate(BaseModel):
    """简历状态更新"""
    status: str


class ResumeResponse(ResumeBase, IDSchema, TimestampSchema):
    """简历响应"""
    userId: Optional[UUID] = Field(alias="user_id")
    status: str
    submittedAt: Optional[datetime] = Field(alias="submitted_at")
    resumeUrl: Optional[str] = Field(alias="resume_url")
    conversationSummary: Optional[str] = Field(alias="conversation_summary")
    isMatch: Optional[bool] = Field(None, alias="is_match")
    matchConclusion: Optional[str] = Field(None, alias="match_conclusion")

    @field_serializer('submittedAt')
    def serialize_submitted_at(self, value: Optional[datetime]) -> Optional[str]:
        """格式化提交时间为可读格式"""
        return format_datetime(value)

    model_config = {
        "from_attributes": True,  # 可以直接从模型实例创建
        "populate_by_name": True
    }


class ResumeDetailResponse(ResumeResponse):
    """简历详情响应 - 包含所有关联数据"""
    # 基础字段的alias映射 - 直接映射到数据库字段
    tenantId: Optional[UUID] = Field(alias="tenant_id")
    sourceChannelId: Optional[UUID] = Field(alias="source_channel_id")
    jobId: Optional[UUID] = Field(alias="job_id")
    experienceYears: Optional[str] = Field(alias="experience_years")
    educationLevel: Optional[str] = Field(alias="education_level")
    resumeUrl: Optional[str] = Field(alias="resume_url")
    conversationSummary: Optional[str] = Field(alias="conversation_summary")
    isMatch: Optional[bool] = Field(None, alias="is_match")
    matchConclusion: Optional[str] = Field(None, alias="match_conclusion")

    # 关联数据的alias映射
    workHistory: Optional[List[WorkExperienceBase]] = Field(default=[], alias="work_experiences")
    projectHistory: Optional[List[ProjectExperienceBase]] = Field(default=[], alias="project_experiences")
    educationHistory: Optional[List[EducationHistoryBase]] = Field(default=[], alias="education_histories")
    jobPreferences: Optional[JobPreferenceBase] = Field(None, alias="job_preference")
    aiMatchResults: Optional[List[AIMatchBase]] = Field(default=[], alias="ai_match_results")
    chatHistory: Optional[List[CandidateChatHistoryBase]] = Field(default=[], alias="chat_histories")
    interviews: Optional[List[InterviewResponse]] = Field(default=[])
    emails: Optional[List[EmailLogResponse]] = Field(default=[], alias="email_logs")

    model_config = {
        "from_attributes": False,  # 因为现在传递的是字典而不是模型实例
        "populate_by_name": True
    }


class AIMatchRequest(BaseModel):
    """AI匹配请求"""
    jobId: UUID


class SendEmailRequest(BaseModel):
    """发送邮件请求"""
    subject: str
    content: str
