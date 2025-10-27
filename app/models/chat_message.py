"""
Chat Message model
"""
from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import Base


class ChatMessage(Base):
    """AI聊天消息模型"""
    
    __tablename__ = "chat_messages"
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True, comment="发送该消息的用户ID")
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="聊天会话ID")
    role = Column(String(20), nullable=False, comment="消息角色: user-用户, assistant-AI助手, system-系统")
    content = Column(Text, nullable=False, comment="消息内容")
    message_type = Column(String(50), default='text', index=True,
                         comment="消息类型: text-普通文本, tool_call-工具调用请求, tool_result-工具执行结果, thinking-AI思考过程, code-代码, image-图片, file-文件")
    message_metadata = Column(JSONB, comment="消息元数据（JSONB格式）")
    
    
    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, role={self.role}, message_type={self.message_type})>"

