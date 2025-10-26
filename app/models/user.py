"""
User model
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class User(Base):
    """用户模型"""
    
    __tablename__ = "users"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, comment="用户姓名")
    email = Column(String(255), nullable=False, index=True, comment="邮箱地址")
    password_hash = Column(String(255), nullable=False, comment="密码哈希值（bcrypt加密）")
    role = Column(
        String(20), 
        nullable=False, 
        default="hr", 
        comment="用户角色: admin-管理员, hr-人力资源, recruiter-招聘专员"
    )
    avatar_url = Column(Text, comment="头像URL")
    last_login_at = Column(DateTime(timezone=True), nullable=True, comment="最后登录时间")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 关系
    tenant = relationship("Tenant", back_populates="users")
    settings = relationship("UserSetting", back_populates="user", uselist=False, lazy="selectin")
    jobs = relationship("Job", back_populates="created_by_user", lazy="dynamic")
    chat_sessions = relationship("ChatSession", back_populates="user", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.name}, email={self.email})>"

