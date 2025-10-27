"""
Candidate model
"""
from sqlalchemy import Column, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import Base


class Candidate(Base):
    """候选人模型"""

    __tablename__ = "candidates"

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
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

  
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('tenant_id', 'source', 'source_id', name='uq_candidate_source'),
    )
    
    def __repr__(self) -> str:
        return f"<Candidate(id={self.id}, name={self.name}, source={self.source})>"

