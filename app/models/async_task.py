"""
Async Task model
"""
from datetime import datetime

from sqlalchemy import Column, BigInteger, String, Text, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base


class AsyncTask(Base):
    """异步任务记录模型"""
    
    __tablename__ = "async_tasks"
    
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False, index=True)
    task_type = Column(
        String(50), 
        nullable=False,
        index=True,
        comment="任务类型: resume_parse, email_sync, rpa_job_post, matching等"
    )
    celery_task_id = Column(String(255), unique=True, index=True, comment="Celery任务ID")
    status = Column(
        String(20), 
        default="pending",
        index=True,
        comment="状态: pending, running, completed, failed, retry"
    )
    params = Column(JSONB, comment="任务参数")
    result = Column(JSONB, comment="任务结果")
    error_message = Column(Text, comment="错误信息")
    retry_count = Column(Integer, default=0, comment="重试次数")
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    scheduled_at = Column(DateTime, nullable=True, index=True, comment="计划执行时间")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    
    def __repr__(self) -> str:
        return f"<AsyncTask(id={self.id}, type={self.task_type}, status={self.status})>"

