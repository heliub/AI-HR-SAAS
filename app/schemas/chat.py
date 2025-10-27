"""
Chat schemas
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.base import BaseSchema, TimestampSchema, IDSchema


class ChatSessionBase(BaseModel):
    """聊天会话基础Schema"""
    title: str = Field(..., min_length=1, max_length=200)


class ChatSessionCreate(ChatSessionBase):
    """创建聊天会话"""
    pass


class ChatSessionResponse(ChatSessionBase, IDSchema, TimestampSchema):
    """聊天会话响应"""
    pass


class ChatMessageBase(BaseModel):
    """聊天消息基础Schema"""
    role: str
    content: str


class ChatMessageCreate(ChatMessageBase):
    """创建聊天消息"""
    pass


class ChatMessageResponse(ChatMessageBase, IDSchema):
    """聊天消息响应"""
    userId: Optional[UUID] = Field(None, alias="user_id", serialization_alias="userId")
    timestamp: datetime


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    content: str


class MessagesResponse(BaseModel):
    """消息列表响应"""
    messages: List[ChatMessageResponse]

