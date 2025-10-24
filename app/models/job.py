"""
Job model
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class Job(Base):
    """职位模型"""
    
    __tablename__ = "jobs"
    
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False, index=True)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False, comment="职位标题")
    description = Column(Text, comment="职位描述")
    requirements = Column(JSONB, comment="结构化要求")
    location = Column(String(255), comment="工作地点")
    salary_range = Column(String(100), comment="薪资范围")
    employment_type = Column(
        String(50),
        comment="雇佣类型: full_time, part_time, contract"
    )
    status = Column(
        String(20), 
        default="open",
        index=True,
        comment="状态: open, closed, on_hold"
    )
    published_platforms = Column(JSONB, comment="已发布的平台")
    closed_at = Column(DateTime, nullable=True, comment="关闭时间")
    
    # 关系
    tenant = relationship("Tenant", back_populates="jobs")
    created_by_user = relationship("User", back_populates="jobs")
    resumes = relationship("Resume", back_populates="job", lazy="selectin")
    matching_results = relationship("MatchingResult", back_populates="job", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title={self.title}, status={self.status})>"

