"""
Statistics schemas
"""
from typing import Optional
from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Dashboard统计数据"""
    pendingResumes: int
    upcomingInterviews: int
    activeTasks: int
    openJobs: int


class JobStats(BaseModel):
    """职位统计数据"""
    totalJobs: int
    activeJobs: int
    totalApplicants: int
    draftJobs: int


class ResumeStats(BaseModel):
    """简历统计数据"""
    total: int
    pending: int
    reviewing: int
    interview: int
    offered: int
    rejected: int


class ChannelStats(BaseModel):
    """渠道统计数据"""
    totalChannels: int
    activeChannels: int
    totalApplicants: int
    averageConversion: float


class ConversionRates(BaseModel):
    """转化率"""
    resumeToInterview: float
    interviewToOffer: float
    offerToAccept: float


class FunnelStats(BaseModel):
    """招聘漏斗统计数据"""
    totalResumes: int
    interviewScheduled: int
    offersSent: int
    offersAccepted: int
    conversionRates: ConversionRates

