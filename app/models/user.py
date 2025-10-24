"""
User model
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class User(Base):
    """用户模型"""
    
    __tablename__ = "users"
    
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False, index=True)
    username = Column(String(100), nullable=False, comment="用户名")
    email = Column(String(255), nullable=False, index=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    full_name = Column(String(255), comment="全名")
    role = Column(
        String(50), 
        nullable=False, 
        default="hr", 
        comment="角色: admin, hr"
    )
    language = Column(
        String(10), 
        default="en", 
        comment="用户语言: en, zh, id"
    )
    status = Column(
        String(20), 
        nullable=False, 
        default="active",
        comment="状态: active, inactive, suspended"
    )
    settings = Column(JSONB, comment="用户个人配置")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    
    # 关系
    tenant = relationship("Tenant", back_populates="users")
    conversations = relationship("Conversation", back_populates="user", lazy="selectin")
    jobs = relationship("Job", back_populates="created_by_user", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

