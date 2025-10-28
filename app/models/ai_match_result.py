"""
AI Match Result model
"""
from sqlalchemy import Column, Integer, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class AIMatchResult(Base):
    """AI简历匹配结果模型"""
    
    __tablename__ = "ai_match_results"
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True, comment="创建该匹配结果的HR用户ID")
    resume_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="简历ID")
    job_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="职位ID")
    is_match = Column(Boolean, nullable=False, comment="是否匹配")
    match_score = Column(Integer, comment="匹配分数（0-100）")
    reason = Column(Text, comment="AI分析原因")
    strengths = Column(Text, comment="优势列表（多个优势用分隔符分开，如逗号）")
    weaknesses = Column(Text, comment="劣势列表（多个劣势用分隔符分开，如逗号）")
    recommendation = Column(Text, comment="AI推荐意见")
    analyzed_at = Column(DateTime(timezone=True), comment="AI分析时间")
    
    
    def __repr__(self) -> str:
        return f"<AIMatchResult(id={self.id}, match_score={self.match_score}, is_match={self.is_match})>"

