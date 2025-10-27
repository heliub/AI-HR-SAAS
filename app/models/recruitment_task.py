"""
Recruitment Task model
"""
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class RecruitmentTask(Base):
    """AI招聘任务模型"""
    
    __tablename__ = "recruitment_tasks"
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True, comment="处理该任务的HR用户ID")
    job_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="职位ID")
    job_title = Column(String(200), nullable=False, comment="职位标题（冗余字段）")
    status = Column(String(20), nullable=False, default="not-started", index=True,
                   comment="任务状态: not-started-未开始, in-progress-进行中, paused-已暂停, completed-已完成")
    created_by = Column(UUID(as_uuid=True), comment="创建人用户ID")
    channels_published = Column(Integer, default=0, comment="已发布渠道数")
    total_channels = Column(Integer, default=0, comment="计划发布总渠道数")
    resumes_viewed = Column(Integer, default=0, comment="AI已浏览简历数")
    greetings_sent = Column(Integer, default=0, comment="AI已发送问候数")
    conversations_active = Column(Integer, default=0, comment="AI活跃对话数")
    resumes_requested = Column(Integer, default=0, comment="AI请求完整简历数")
    resumes_received = Column(Integer, default=0, comment="AI收到完整简历数")
    interviews_scheduled = Column(Integer, default=0, comment="AI安排面试数")
    completed_at = Column(DateTime(timezone=True), comment="任务完成时间")
    
    
    def __repr__(self) -> str:
        return f"<RecruitmentTask(id={self.id}, job_title={self.job_title}, status={self.status})>"

