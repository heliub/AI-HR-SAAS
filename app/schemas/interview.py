"""
Interview schemas
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, date, time
from pydantic import BaseModel, Field
from app.schemas.base import BaseSchema, TimestampSchema, IDSchema


class InterviewBase(BaseModel):
    """面试基础Schema"""
    candidateId: UUID = Field(alias="candidate_id")
    candidateName: str = Field(alias="candidate_name")
    position: str
    interviewDate: date = Field(alias="interview_date")
    interviewTime: time = Field(alias="interview_time")
    interviewer: str
    interviewerTitle: Optional[str] = Field(None, alias="interviewer_title")
    type: str
    location: Optional[str] = None
    meetingLink: Optional[str] = Field(None, alias="meeting_link")
    notes: Optional[str] = None


class InterviewCreate(InterviewBase):
    """创建面试"""
    pass


class InterviewUpdate(BaseModel):
    """更新面试"""
    date: Optional[date] = None
    time: Optional[time] = None
    interviewer: Optional[str] = None
    interviewerTitle: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    meetingLink: Optional[str] = None
    notes: Optional[str] = None


class InterviewCancelRequest(BaseModel):
    """取消面试请求"""
    reason: str


class InterviewResponse(InterviewBase, IDSchema, TimestampSchema):
    """面试响应"""
    status: str
    feedback: Optional[str] = None
    rating: Optional[int] = None
    cancelledAt: Optional[datetime] = Field(alias="cancelled_at")
    cancellationReason: Optional[str] = Field(alias="cancellation_reason")

