"""
Chat endpoints
"""
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.chat import (
    ChatSessionCreate, ChatSessionResponse,
    SendMessageRequest, MessagesResponse
)
from app.schemas.base import APIResponse
from app.models.user import User

router = APIRouter()


@router.get("/sessions", response_model=APIResponse)
async def get_chat_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取聊天会话列表"""
    # TODO: 实现会话列表查询
    return APIResponse(
        code=200,
        message="成功",
        data={"list": []}
    )


@router.post("/sessions", response_model=APIResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新会话"""
    # TODO: 实现会话创建
    from datetime import datetime
    return APIResponse(
        code=200,
        message="会话创建成功",
        data={"id": "new-session-id", "title": session_data.title, "createdAt": datetime.utcnow().isoformat()}
    )


@router.get("/sessions/{session_id}/messages", response_model=APIResponse)
async def get_chat_messages(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取聊天历史"""
    # TODO: 实现消息列表查询
    return APIResponse(
        code=200,
        message="成功",
        data={"messages": []}
    )


@router.post("/sessions/{session_id}/messages", response_model=APIResponse)
async def send_message(
    session_id: UUID,
    message_data: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送消息"""
    # TODO: 实现消息发送和AI响应
    from datetime import datetime
    return APIResponse(
        code=200,
        message="成功",
        data={
            "id": "new-message-id",
            "role": "assistant",
            "content": "我已经为你筛选了最近的简历...",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

