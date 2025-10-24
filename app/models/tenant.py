"""
Tenant model
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class Tenant(Base):
    """租户模型"""
    
    __tablename__ = "tenants"
    
    name = Column(String(255), nullable=False, comment="租户名称")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="租户标识码")
    status = Column(
        String(20), 
        nullable=False, 
        default="active", 
        index=True,
        comment="状态: active, suspended, deleted"
    )
    settings = Column(JSONB, comment="租户配置")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    
    # 关系
    users = relationship("User", back_populates="tenant", lazy="selectin")
    jobs = relationship("Job", back_populates="tenant", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name}, code={self.code})>"

