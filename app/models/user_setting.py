"""
User Setting model
"""
from sqlalchemy import Column, String, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class UserSetting(Base):
    """用户设置模型"""
    
    __tablename__ = "user_settings"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    language = Column(String(10), default='zh', comment="界面语言: zh-中文, en-英文, id-印尼语")
    email_notifications = Column(Boolean, default=True, comment="是否开启邮件通知")
    task_reminders = Column(Boolean, default=True, comment="是否开启任务提醒")
    
    # 关系
    user = relationship("User", back_populates="settings")
    
    def __repr__(self) -> str:
        return f"<UserSetting(id={self.id}, user_id={self.user_id})>"

