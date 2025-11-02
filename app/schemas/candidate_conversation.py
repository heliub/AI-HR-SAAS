"""
Candidate Conversation schemas - 候选人会话相关Schema
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.base import TimestampSchema


class ConversationMessageResponse(TimestampSchema):
    """会话消息响应"""
    id: UUID
    conversationId: Optional[UUID] = Field(None, alias="conversation_id")
    resumeId: UUID = Field(alias="resume_id")
    sender: str = Field(..., description="消息发送者: candidate-候选人, ai-AI助手")
    message: str = Field(..., description="消息内容")
    messageType: str = Field(alias="message_type", description="消息类型: text, greeting, question, answer, closing")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ConversationMessageListResponse(BaseModel):
    """消息列表响应"""
    total: int = Field(..., description="消息总数")
    messages: List[ConversationMessageResponse] = Field(..., description="消息列表")


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    content: str = Field(..., min_length=1, max_length=2000, description="消息内容")

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "你好，请问这个职位的薪资范围是多少？"
            }
        }
    }


class CreateConversationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    """创建会话请求"""
    resumeId: UUID = Field(..., alias="resume_id", description="候选人简历ID")
    jobId: UUID = Field(..., alias="job_id", description="职位ID")



class CandidateConversationResponse(TimestampSchema):
    """候选人会话响应"""
    id: UUID
    tenantId: UUID = Field(alias="tenant_id")
    userId: UUID = Field(alias="user_id")
    resumeId: UUID = Field(alias="resume_id")
    jobId: UUID = Field(alias="job_id")
    status: str = Field(..., description="会话状态: opened, ongoing, interrupted, ended, deleted")
    stage: str = Field(..., description="沟通阶段: greeting, questioning, intention, matched")
    summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ConversationListResponse(BaseModel):
    """会话列表响应"""
    total: int = Field(..., description="会话总数")
    conversations: List[CandidateConversationResponse] = Field(..., description="会话列表")


class SendMessageResponse(BaseModel):
    """发送消息响应"""
    candidateMessage: ConversationMessageResponse = Field(..., alias="candidate_message", description="候选人发送的消息")
    aiMessage: Optional[ConversationMessageResponse] = Field(None, alias="ai_message", description="AI回复的消息")
    action: str = Field(..., description="流程动作: send_message-发送消息, suspend-转人工, none-无动作")
    conversationStatus: str = Field(alias="conversation_status", description="会话状态")
    conversationStage: str = Field(alias="conversation_stage", description="会话阶段")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CandidateConversationDetailResponse(CandidateConversationResponse):
    """候选人会话详情响应（包含最新消息）"""
    latestMessages: List[ConversationMessageResponse] = Field(
        default=[],
        alias="latest_messages",
        description="最新10条消息"
    )
    messageCount: int = Field(0, alias="message_count", description="消息总数")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
