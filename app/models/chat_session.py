"""
Chat Session model
"""
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class ChatSession(Base):
    """AI聊天会话模型"""
    
    __tablename__ = "chat_sessions"
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="用户ID")
    title = Column(String(200), nullable=False, comment="会话标题")
    
    
    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, title={self.title})>"

