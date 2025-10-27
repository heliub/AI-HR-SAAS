"""
Chat service
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.services.base import BaseService
from app.core.exceptions import NotFoundException


class ChatService(BaseService[ChatSession]):
    """聊天服务"""

    def __init__(self):
        super().__init__(ChatSession)

    async def get_chat_sessions(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        *,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[List[ChatSession], int]:
        """获取聊天会话列表"""
        query = select(ChatSession).where(
            and_(
                ChatSession.tenant_id == tenant_id,
                ChatSession.user_id == user_id
            )
        )

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)

        # 按更新时间倒序
        query = query.order_by(ChatSession.updated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        sessions = result.scalars().all()

        return list(sessions), total or 0

    async def create_chat_session(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        user_id: UUID,
        title: str
    ) -> ChatSession:
        """创建聊天会话"""
        session = ChatSession(
            tenant_id=tenant_id,
            user_id=user_id,
            title=title
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        return session

    async def get_chat_messages(
        self,
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID,
        limit: int = 50
    ) -> List[ChatMessage]:
        """获取聊天消息"""
        # 验证会话权限
        session_query = select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            )
        )
        session = await db.scalar(session_query)
        if not session:
            raise NotFoundException("Chat session not found")

        # 获取消息
        query = select(ChatMessage).where(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).limit(limit)

        result = await db.execute(query)
        messages = result.scalars().all()

        return list(messages)

    async def send_message(
        self,
        db: AsyncSession,
        *,
        session_id: UUID,
        user_id: UUID,
        content: str,
        role: str,
        message_type: str = "text",
        metadata: Optional[dict] = None
    ) -> ChatMessage:
        """发送消息"""
        # 验证会话权限
        session_query = select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            )
        )
        session = await db.scalar(session_query)
        if not session:
            raise NotFoundException("Chat session not found")

        # 创建消息
        message = ChatMessage(
            tenant_id=session.tenant_id,
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            metadata=metadata
        )
        db.add(message)

        # 更新会话最后更新时间
        session.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(message)

        return message

    async def delete_chat_session(
        self,
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID
    ) -> bool:
        """删除聊天会话"""
        # 验证会话权限
        session_query = select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            )
        )
        session = await db.scalar(session_query)
        if not session:
            return False

        # 删除会话相关的消息
        messages_query = select(ChatMessage).where(
            ChatMessage.session_id == session_id
        )
        messages = await db.execute(messages_query)
        for message in messages.scalars():
            await db.delete(message)

        # 删除会话
        await db.delete(session)
        await db.commit()

        return True

    async def get_session_by_id(
        self,
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID
    ) -> Optional[ChatSession]:
        """根据ID获取会话"""
        query = select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()