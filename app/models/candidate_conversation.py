"""
Candidate Conversation model
"""
from typing import Optional

from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class CandidateConversation(Base):
    """候选人会话模型"""
    
    __tablename__ = "candidate_conversations"
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="负责该会话的HR用户ID")
    resume_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="候选人简历ID")
    job_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="关联职位ID")
    status = Column(String(20), nullable=False, default="opened", index=True, comment="会话状态: opened-会话开启, ongoing-沟通中, interrupted-中断, ended-会话结束, deleted-已删除")
    stage = Column(String(20), nullable=False, default="greeting", comment="沟通阶段: greeting-开场白阶段, questioning-问题询问阶段, intention-职位意向询问阶段, matched-撮合成功")
    summary = Column(Text, comment="会话总结（AI生成）")
    
    def __repr__(self) -> str:
        return f"<CandidateConversation(id={self.id}, resume_id={self.resume_id}, job_id={self.job_id}, status={self.status})>"
