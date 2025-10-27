"""
Chat endpoints
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.chat import (
    ChatSessionCreate, ChatSessionResponse,
    SendMessageRequest
)
from app.schemas.base import APIResponse, PaginatedResponse
from app.services.chat_service import ChatService
from app.models.user import User

router = APIRouter()


@router.get("/sessions", response_model=APIResponse)
async def get_chat_sessions(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取聊天会话列表"""
    chat_service = ChatService()

    sessions, total = await chat_service.get_chat_sessions(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        page=page,
        page_size=pageSize
    )

    session_responses = [ChatSessionResponse.model_validate(session) for session in sessions]

    paginated_data = PaginatedResponse(
        total=total,
        page=page,
        pageSize=pageSize,
        list=session_responses
    )

    return APIResponse(
        code=200,
        message="成功",
        data=paginated_data.model_dump()
    )


@router.post("/sessions", response_model=APIResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新会话"""
    chat_service = ChatService()

    session = await chat_service.create_chat_session(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        title=session_data.title
    )

    session_response = ChatSessionResponse.model_validate(session)

    return APIResponse(
        code=200,
        message="会话创建成功",
        data=session_response.model_dump()
    )


@router.get("/sessions/{session_id}/messages", response_model=APIResponse)
async def get_chat_messages(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取聊天历史"""
    chat_service = ChatService()

    try:
        messages = await chat_service.get_chat_messages(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )

        messages_data = [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat()
            }
            for msg in messages
        ]

        return APIResponse(
            code=200,
            message="成功",
            data={"messages": messages_data}
        )
    except AttributeError:
        # 会话不存在或其他属性错误
        return APIResponse(
            code=404,
            message="会话不存在"
        )
    except Exception:
        raise HTTPException(status_code=404, detail="会话不存在")


@router.post("/sessions/{session_id}/messages", response_model=APIResponse)
async def send_message(
    session_id: UUID,
    message_data: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送消息"""
    chat_service = ChatService()

    try:
        # 发送用户消息
        await chat_service.send_message(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            content=message_data.content,
            role="user",
            message_type="text"
        )

        # 生成智能AI响应
        ai_response_content = await _generate_ai_response(message_data.content)

        ai_response = await chat_service.send_message(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            content=ai_response_content,
            role="assistant",
            message_type="text"
        )

        return APIResponse(
            code=200,
            message="成功",
            data={
                "id": str(ai_response.id),
                "role": ai_response.role,
                "content": ai_response.content,
                "timestamp": ai_response.created_at.isoformat()
            }
        )

    except AttributeError:
        # 会话不存在或其他属性错误
        return APIResponse(
            code=404,
            message="会话不存在"
        )
    except Exception:
        raise HTTPException(status_code=404, detail="会话不存在")


async def _generate_ai_response(user_message: str) -> str:
    """
    生成AI响应内容
    这里可以根据用户消息内容进行智能回复
    """
    user_message_lower = user_message.lower()

    # 简单的规则匹配回复逻辑
    if "简历" in user_message_lower and "筛选" in user_message_lower:
        return f"我已收到您的简历筛选请求。正在为您分析数据库中的简历匹配情况，请稍等..."

    elif "面试" in user_message_lower and "安排" in user_message_lower:
        return "我可以帮您安排面试。请提供候选人姓名、职位和期望的面试时间，我将为您协调安排。"

    elif "统计" in user_message_lower or "数据" in user_message_lower:
        return "我可以为您提供各类招聘统计数据，包括职位发布情况、简历投递量、面试通过率等。您想查看哪方面的数据？"

    elif "帮助" in user_message_lower or "功能" in user_message_lower:
        return "我是您的AI招聘助手，可以帮您：\n• 筛选和匹配简历\n• 安排面试\n• 提供招聘统计数据\n• 生成职位描述\n• 发送邮件通知\n\n请告诉我您需要什么帮助！"

    else:
        return "我理解您的需求。作为AI招聘助手，我可以帮您处理简历筛选、面试安排、数据分析等招聘相关工作。请更具体地描述您的需求，我会为您提供精准的帮助。"

