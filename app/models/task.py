"""
Task model
"""
from datetime import datetime

from sqlalchemy import Column, BigInteger, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class Task(Base):
    """任务实例模型"""
    
    __tablename__ = "tasks"
    
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(
        BigInteger, 
        ForeignKey("conversations.id"), 
        nullable=False, 
        index=True
    )
    task_type = Column(
        String(50), 
        nullable=False, 
        index=True,
        comment="任务类型: job_discussion, progress_inquiry, candidate_review等"
    )
    task_name = Column(String(500), comment="任务名称")
    context = Column(JSONB, comment="任务上下文信息")
    related_job_id = Column(BigInteger, nullable=True, comment="关联的职位ID")
    status = Column(
        String(20), 
        default="active",
        index=True,
        comment="状态: active, inactive, completed, archived"
    )
    last_active_at = Column(
        DateTime, 
        nullable=False, 
        default=datetime.utcnow,
        index=True,
        comment="最后活跃时间"
    )
    
    # 关系
    conversation = relationship("Conversation", back_populates="tasks")
    messages = relationship("Message", back_populates="task", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<Task(id={self.id}, type={self.task_type}, status={self.status})>"

