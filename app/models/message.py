"""
Message model
"""
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import Base


class Message(Base):
    """消息模型"""
    
    __tablename__ = "messages"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id"),
        nullable=False,
        index=True
    )
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True, index=True)
    role = Column(
        String(20), 
        nullable=False,
        comment="角色: user, assistant, system"
    )
    content = Column(Text, nullable=False, comment="消息内容")
    meta_info = Column("metadata", JSONB, comment="附加信息（意图识别结果等）")
    
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role})>"

