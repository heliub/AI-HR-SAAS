"""
Conversation schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.base import TimestampSchema, IDSchema


class MessageCreate(BaseModel):
    """创建消息"""
    content: str = Field(..., min_length=1)
    conversationId: Optional[int] = Field(alias="conversation_id")


class MessageResponse(IDSchema, TimestampSchema):
    """消息响应"""
    conversationId: int = Field(alias="conversation_id")
    taskId: Optional[int] = Field(alias="task_id")
    role: str
    content: str
    metaInfo: Optional[dict] = Field(alias="meta_info")


class ConversationResponse(IDSchema, TimestampSchema):
    """会话响应"""
    tenantId: int = Field(alias="tenant_id")
    userId: int = Field(alias="user_id")
    title: Optional[str] = None


class ConversationDetailResponse(ConversationResponse):
    """会话详情响应"""
    messages: List[MessageResponse] = []


class ChatResponse(BaseModel):
    """对话响应"""
    conversationId: int = Field(alias="conversation_id")
    taskId: int = Field(alias="task_id")
    taskType: str = Field(alias="task_type")
    response: str
    intent: str

