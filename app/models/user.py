"""
User model
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class User(Base):
    """用户模型"""
    
    __tablename__ = "users"
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
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
      
    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.name}, email={self.email})>"

