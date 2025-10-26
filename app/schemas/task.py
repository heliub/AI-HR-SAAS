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
    jobId: UUID
    jobTitle: str


class RecruitmentTaskCreate(RecruitmentTaskBase):
    """创建招聘任务"""
    totalChannels: int = 0


class RecruitmentTaskStatusUpdate(BaseModel):
    """任务状态更新"""
    status: str


class RecruitmentTaskProgressUpdate(BaseModel):
    """任务进度更新"""
    channelsPublished: Optional[int] = None
    resumesViewed: Optional[int] = None
    greetingsSent: Optional[int] = None
    conversationsActive: Optional[int] = None
    resumesRequested: Optional[int] = None
    resumesReceived: Optional[int] = None
    interviewsScheduled: Optional[int] = None


class RecruitmentTaskResponse(RecruitmentTaskBase, IDSchema, TimestampSchema):
    """招聘任务响应"""
    status: str
    createdBy: Optional[str] = None
    channelsPublished: int = 0
    totalChannels: int = 0
    resumesViewed: int = 0
    greetingsSent: int = 0
    conversationsActive: int = 0
    resumesRequested: int = 0
    resumesReceived: int = 0
    interviewsScheduled: int = 0
    completedAt: Optional[datetime] = None

