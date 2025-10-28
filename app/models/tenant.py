"""
Tenant model
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Tenant(Base):
    """租户模型"""
    
    __tablename__ = "tenants"
    
    name = Column(String(200), nullable=False, comment="租户名称")
    company_name = Column(String(200), comment="公司名称")
    contact_name = Column(String(100), comment="联系人姓名")
    contact_email = Column(String(255), comment="联系人邮箱")
    contact_phone = Column(String(50), comment="联系人电话")
    plan_type = Column(String(50), default='basic', comment="套餐类型: basic-基础版, pro-专业版, enterprise-企业版")
    status = Column(
        String(20),
        default="active",
        index=True,
        comment="状态: active-激活, inactive-停用, suspended-暂停"
    )
    max_users = Column(Integer, default=10, comment="最大用户数")
    max_jobs = Column(Integer, default=50, comment="最大职位数")
    expires_at = Column(DateTime(timezone=True), comment="到期时间")
    
    
    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name})>"

