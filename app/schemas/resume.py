"""
Resume schemas
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field
from app.schemas.base import BaseSchema, TimestampSchema, IDSchema


class WorkExperienceBase(BaseModel):
    """工作经历基础Schema"""
    company: str
    position: str
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    description: Optional[str] = None


class ProjectExperienceBase(BaseModel):
    """项目经历基础Schema"""
    name: str
    role: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[List[str]] = None


class EducationHistoryBase(BaseModel):
    """教育经历基础Schema"""
    school: str
    degree: Optional[str] = None
    major: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None


class JobPreferenceBase(BaseModel):
    """求职意向基础Schema"""
    expectedSalary: Optional[str] = Field(None, alias="expected_salary", serialization_alias="expectedSalary")
    preferredLocations: Optional[List[str]] = Field(None, alias="preferred_locations", serialization_alias="preferredLocations")
    jobType: Optional[str] = Field(None, alias="job_type", serialization_alias="jobType")
    availableDate: Optional[date] = Field(None, alias="available_date", serialization_alias="availableDate")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class AIMatchBase(BaseModel):
    """AI匹配基础Schema"""
    isMatch: bool
    score: Optional[int] = None
    reason: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    recommendation: Optional[str] = None


class CandidateChatHistoryBase(BaseModel):
    """候选人聊天历史基础Schema"""
    sender: str
    message: str
    timestamp: datetime


class ResumeBase(BaseModel):
    """简历基础Schema"""
    candidateName: str = Field(alias="candidate_name", serialization_alias="candidateName")
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    position: str
    source: Optional[str] = None
    experienceYears: Optional[str] = Field(None, alias="experience_years", serialization_alias="experienceYears")
    educationLevel: Optional[str] = Field(None, alias="education_level", serialization_alias="educationLevel")
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    school: Optional[str] = None
    major: Optional[str] = None
    skills: Optional[List[str]] = None


class ResumeCreate(ResumeBase):
    """创建简历"""
    jobId: Optional[UUID] = None


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
    userId: Optional[UUID] = Field(None, alias="user_id", serialization_alias="userId")
    status: str
    submittedAt: Optional[datetime] = Field(None, alias="submitted_at", serialization_alias="submittedAt")
    resumeUrl: Optional[str] = Field(None, alias="resume_url", serialization_alias="resumeUrl")
    workHistory: Optional[List[WorkExperienceBase]] = Field(None, alias="work_history", serialization_alias="workHistory")
    projectHistory: Optional[List[ProjectExperienceBase]] = Field(None, alias="project_history", serialization_alias="projectHistory")
    educationHistory: Optional[List[EducationHistoryBase]] = Field(None, alias="education_history", serialization_alias="educationHistory")
    jobPreferences: Optional[JobPreferenceBase] = Field(None, alias="job_preferences", serialization_alias="jobPreferences")
    aiMatch: Optional[AIMatchBase] = Field(None, alias="ai_match", serialization_alias="aiMatch")
    aiChatHistory: Optional[List[CandidateChatHistoryBase]] = Field(None, alias="ai_chat_history", serialization_alias="aiChatHistory")
    conversationSummary: Optional[str] = Field(None, alias="conversation_summary", serialization_alias="conversationSummary")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }


class AIMatchRequest(BaseModel):
    """AI匹配请求"""
    jobId: UUID


class SendEmailRequest(BaseModel):
    """发送邮件请求"""
    subject: str
    content: str
