"""
Conversation model
"""
from sqlalchemy import Column, BigInteger, String, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base


class Conversation(Base):
    """会话模型"""
    
    __tablename__ = "conversations"
    
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), comment="会话标题")
    
    # 关系
    user = relationship("User", back_populates="conversations")
    tasks = relationship("Task", back_populates="conversation", lazy="selectin")
    messages = relationship("Message", back_populates="conversation", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title})>"

