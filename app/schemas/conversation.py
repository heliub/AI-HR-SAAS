"""
Conversation schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.base import TimestampSchema, IDSchema


class MessageCreate(BaseModel):
    """创建消息"""
    content: str = Field(..., min_length=1)
    conversation_id: Optional[int] = None


class MessageResponse(IDSchema, TimestampSchema):
    """消息响应"""
    conversation_id: int
    task_id: Optional[int] = None
    role: str
    content: str
    meta_info: Optional[dict] = None


class ConversationResponse(IDSchema, TimestampSchema):
    """会话响应"""
    tenant_id: int
    user_id: int
    title: Optional[str] = None


class ConversationDetailResponse(ConversationResponse):
    """会话详情响应"""
    messages: List[MessageResponse] = []


class ChatResponse(BaseModel):
    """对话响应"""
    conversation_id: int
    task_id: int
    task_type: str
    response: str
    intent: str

