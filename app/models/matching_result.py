"""
Matching Result model
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, BigInteger, String, Text, ForeignKey, DateTime, DECIMAL, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class MatchingResult(Base):
    """人岗匹配结果模型"""
    
    __tablename__ = "matching_results"
    
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False, index=True)
    job_id = Column(BigInteger, ForeignKey("jobs.id"), nullable=False, index=True)
    resume_id = Column(BigInteger, ForeignKey("resumes.id"), nullable=False, index=True)
    candidate_id = Column(BigInteger, ForeignKey("candidates.id"), nullable=False, index=True)
    score = Column(DECIMAL(5, 2), comment="匹配分数 0-100")
    result = Column(
        String(20),
        comment="匹配结果: excellent, good, fair, poor"
    )
    reasoning = Column(Text, comment="匹配理由")
    details = Column(JSONB, comment="详细匹配信息")
    status = Column(
        String(20), 
        default="pending_review",
        index=True,
        comment="状态: pending_review, accepted, rejected"
    )
    reviewed_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True, comment="审核时间")
    
    # 关系
    job = relationship("Job", back_populates="matching_results")
    resume = relationship("Resume", back_populates="matching_results")
    candidate = relationship("Candidate", back_populates="matching_results")
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('job_id', 'resume_id', name='uq_matching_job_resume'),
    )
    
    def __repr__(self) -> str:
        return f"<MatchingResult(id={self.id}, score={self.score}, result={self.result})>"

