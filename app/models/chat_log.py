"""
Chat Mediation Log model
"""
from datetime import datetime

from sqlalchemy import Column, BigInteger, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base


class ChatMediationLog(Base):
    """聊天撮合日志模型"""
    
    __tablename__ = "chat_mediation_logs"
    
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False, index=True)
    candidate_id = Column(
        BigInteger, 
        ForeignKey("candidates.id"), 
        nullable=False, 
        index=True
    )
    job_id = Column(BigInteger, ForeignKey("jobs.id"), nullable=True)
    platform = Column(
        String(50), 
        nullable=False,
        index=True,
        comment="平台: linkedin, jobstreet"
    )
    platform_conversation_id = Column(
        String(255),
        index=True,
        comment="平台会话ID"
    )
    message_type = Column(
        String(20),
        comment="消息类型: outbound, inbound"
    )
    message_content = Column(Text, comment="消息内容")
    ai_generated = Column(Boolean, default=False, comment="是否AI生成")
    sent_at = Column(DateTime, nullable=True, comment="发送时间")
    
    # 关系
    candidate = relationship("Candidate", back_populates="chat_logs")
    
    def __repr__(self) -> str:
        return f"<ChatMediationLog(id={self.id}, platform={self.platform}, type={self.message_type})>"

