"""
Conversation endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.conversation import MessageCreate, ChatResponse
from app.services.conversation_service import ConversationService
from app.models.user import User

router = APIRouter()


@router.post("/messages", response_model=ChatResponse)
async def send_message(
    message: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送消息并获取AI响应"""
    conversation_service = ConversationService()
    
    result = await conversation_service.process_message(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        message_content=message.content,
        conversation_id=message.conversation_id,
        user_language=current_user.language
    )
    
    return ChatResponse(**result)

