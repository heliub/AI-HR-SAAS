"""
Candidate Chat History model
"""
from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import Base


class CandidateChatHistory(Base):
    """候选人AI聊天历史模型"""
    
    __tablename__ = "candidate_chat_history"
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
    resume_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="简历ID")
    sender = Column(String(20), nullable=False, comment="发送者: ai-AI助手, candidate-候选人")
    message = Column(Text, nullable=False, comment="消息内容")
    message_type = Column(String(50), default='text', index=True,
                         comment="消息类型: text-普通文本, greeting-问候, question-提问, answer-回答, document_request-文档请求, schedule-日程安排")
    # message_metadata = Column(JSONB, comment="消息元数据（JSONB格式）")  # 暂时注释掉，数据库表中没有此字段
    
    
    def __repr__(self) -> str:
        return f"<CandidateChatHistory(id={self.id}, sender={self.sender})>"

