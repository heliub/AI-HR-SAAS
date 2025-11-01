"""
Conversation Question Tracking model
"""
from typing import Optional

from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class ConversationQuestionTracking(Base):
    """会话问题跟踪模型"""
    
    __tablename__ = "conversation_question_tracking"
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="执行问题的HR用户ID")
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="会话ID")
    question_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="问题ID（关联job_questions表）")
    job_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="职位ID（冗余字段，提高查询效率）")
    resume_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="简历ID（冗余字段，提高查询效率）")
    question = Column(Text, nullable=False, comment="问题内容（冗余字段，提高查询效率）")
    status = Column(String(20), nullable=False, default="pending", index=True, comment="问题状态: pending-待处理, ongoing-进行中, completed-已完成, skipped-已跳过, deleted-已删除")
    is_satisfied = Column(Boolean, comment="是否满足要求（考察类问题）")
    
    def __repr__(self) -> str:
        return f"<ConversationQuestionTracking(id={self.id}, conversation_id={self.conversation_id}, question_id={self.question_id}, status={self.status})>"
