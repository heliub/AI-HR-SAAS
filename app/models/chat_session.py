"""
Chat Session model
"""
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class ChatSession(Base):
    """AI聊天会话模型"""
    
    __tablename__ = "chat_sessions"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False, comment="会话标题")
    
    # 关系
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, title={self.title})>"

