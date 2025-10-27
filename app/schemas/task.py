"""
Recruitment Task schemas
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.base import BaseSchema, TimestampSchema, IDSchema


class RecruitmentTaskBase(BaseModel):
    """招聘任务基础Schema"""
    jobId: UUID = Field(alias="job_id")
    jobTitle: str = Field(alias="job_title")


class RecruitmentTaskCreate(RecruitmentTaskBase):
    """创建招聘任务"""
    totalChannels: int = Field(default=0, alias="total_channels")


class RecruitmentTaskStatusUpdate(BaseModel):
    """任务状态更新"""
    status: str


class RecruitmentTaskProgressUpdate(BaseModel):
    """任务进度更新"""
    channelsPublished: Optional[int] = Field(None, alias="channels_published")
    resumesViewed: Optional[int] = Field(None, alias="resumes_viewed")
    greetingsSent: Optional[int] = Field(None, alias="greetings_sent")
    conversationsActive: Optional[int] = Field(None, alias="conversations_active")
    resumesRequested: Optional[int] = Field(None, alias="resumes_requested")
    resumesReceived: Optional[int] = Field(None, alias="resumes_received")
    interviewsScheduled: Optional[int] = Field(None, alias="interviews_scheduled")


class RecruitmentTaskResponse(RecruitmentTaskBase, IDSchema, TimestampSchema):
    """招聘任务响应"""
    userId: Optional[UUID] = Field(None, alias="user_id")
    status: str
    createdBy: Optional[UUID] = Field(None, alias="created_by")
    channelsPublished: int = Field(default=0, alias="channels_published")
    totalChannels: int = Field(default=0, alias="total_channels")
    resumesViewed: int = Field(default=0, alias="resumes_viewed")
    greetingsSent: int = Field(default=0, alias="greetings_sent")
    conversationsActive: int = Field(default=0, alias="conversations_active")
    resumesRequested: int = Field(default=0, alias="resumes_requested")
    resumesReceived: int = Field(default=0, alias="resumes_received")
    interviewsScheduled: int = Field(default=0, alias="interviews_scheduled")
    completedAt: Optional[datetime] = Field(None, alias="completed_at")

