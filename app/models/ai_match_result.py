"""
AI Match Result model
"""
from sqlalchemy import Column, String, ForeignKey, Integer, Text, ARRAY, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class AIMatchResult(Base):
    """AI简历匹配结果模型"""
    
    __tablename__ = "ai_match_results"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    is_match = Column(Boolean, nullable=False, comment="是否匹配")
    match_score = Column(Integer, comment="匹配分数（0-100）")
    reason = Column(Text, comment="AI分析原因")
    strengths = Column(ARRAY(Text), comment="优势列表（TEXT数组）")
    weaknesses = Column(ARRAY(Text), comment="劣势列表（TEXT数组）")
    recommendation = Column(Text, comment="AI推荐意见")
    analyzed_at = Column(DateTime(timezone=True), comment="AI分析时间")
    
    # 关系
    resume = relationship("Resume", back_populates="ai_match_results")
    job = relationship("Job", back_populates="ai_match_results")
    
    def __repr__(self) -> str:
        return f"<AIMatchResult(id={self.id}, match_score={self.match_score}, is_match={self.is_match})>"

