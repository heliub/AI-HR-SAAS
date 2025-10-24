"""
Candidate model
"""
from sqlalchemy import Column, BigInteger, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class Candidate(Base):
    """候选人模型"""
    
    __tablename__ = "candidates"
    
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, comment="姓名")
    email = Column(String(255), index=True, comment="邮箱")
    phone = Column(String(50), comment="电话")
    source = Column(
        String(50),
        index=True,
        comment="来源: linkedin, jobstreet, email, manual"
    )
    source_id = Column(String(255), comment="来源平台的ID")
    profile_data = Column(JSONB, comment="候选人档案数据")
    
    # 关系
    resumes = relationship("Resume", back_populates="candidate", lazy="selectin")
    matching_results = relationship("MatchingResult", back_populates="candidate", lazy="selectin")
    chat_logs = relationship("ChatMediationLog", back_populates="candidate", lazy="selectin")
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('tenant_id', 'source', 'source_id', name='uq_candidate_source'),
    )
    
    def __repr__(self) -> str:
        return f"<Candidate(id={self.id}, name={self.name}, source={self.source})>"

