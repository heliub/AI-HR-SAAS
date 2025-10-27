"""
Conversation model
"""
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Conversation(Base):
    """会话模型"""
    
    __tablename__ = "conversations"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), comment="会话标题")
    
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title})>"

