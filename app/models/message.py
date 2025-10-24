"""
Message model
"""
from sqlalchemy import Column, BigInteger, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class Message(Base):
    """消息模型"""
    
    __tablename__ = "messages"
    
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False, index=True)
    conversation_id = Column(
        BigInteger, 
        ForeignKey("conversations.id"), 
        nullable=False, 
        index=True
    )
    task_id = Column(BigInteger, ForeignKey("tasks.id"), nullable=True, index=True)
    role = Column(
        String(20), 
        nullable=False,
        comment="角色: user, assistant, system"
    )
    content = Column(Text, nullable=False, comment="消息内容")
    meta_info = Column("metadata", JSONB, comment="附加信息（意图识别结果等）")
    
    # 关系
    conversation = relationship("Conversation", back_populates="messages")
    task = relationship("Task", back_populates="messages")
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role})>"

