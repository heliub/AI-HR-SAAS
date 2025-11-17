"""
Candidate Chat History service for handling candidate chat history-related database operations
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, desc, or_

from app.models.candidate_chat_history import CandidateChatHistory
from app.services.base_service import BaseService
from app.infrastructure.database.session import get_db_context


class CandidateChatHistoryService(BaseService):
    """候选人聊天历史服务类，处理聊天历史相关的数据库操作"""

    def __init__(self, db: Optional[AsyncSession] = None):
        super().__init__(db)

    async def get_messages_by_conversation(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0,
        order_desc: bool = False
    ) -> List[CandidateChatHistory]:
        """
        根据会话ID获取消息列表

        Args:
            conversation_id: 会话ID
            tenant_id: 租户ID
            limit: 返回条数限制（默认100）
            offset: 偏移量（默认0）
            order_desc: 是否倒序（默认False，即按时间正序）

        Returns:
            消息列表
        """
        conditions = [
            CandidateChatHistory.conversation_id == conversation_id,
            CandidateChatHistory.tenant_id == tenant_id
        ]

        query = select(CandidateChatHistory).where(and_(*conditions))

        # 排序：按创建时间
        if order_desc:
            query = query.order_by(desc(CandidateChatHistory.created_at))
        else:
            query = query.order_by(CandidateChatHistory.created_at.asc())

        # 分页
        query = query.limit(limit).offset(offset)
        async with get_db_context() as session:
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_messages_by_resume(
        self,
        resume_id: UUID,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[CandidateChatHistory]:
        """
        根据简历ID获取消息列表（向后兼容旧数据）

        Args:
            resume_id: 简历ID
            tenant_id: 租户ID
            limit: 返回条数限制
            offset: 偏移量

        Returns:
            消息列表
        """
        conditions = [
            CandidateChatHistory.resume_id == resume_id,
            CandidateChatHistory.tenant_id == tenant_id
        ]

        query = (
            select(CandidateChatHistory)
            .where(and_(*conditions))
            .order_by(CandidateChatHistory.created_at.asc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_message(
        self,
        tenant_id: UUID,
        resume_id: UUID,
        sender: str,
        message: str,
        conversation_id: Optional[UUID] = None,
        message_type: str = "text",
    ) -> CandidateChatHistory:
        """
        创建新消息

        Args:
            tenant_id: 租户ID
            resume_id: 简历ID
            sender: 发送者（candidate/ai/system）
            message: 消息内容
            conversation_id: 会话ID（可选，新数据应该提供）
            message_type: 消息类型

        Returns:
            创建的消息对象
        """
        message_data = {
            "tenant_id": tenant_id,
            "resume_id": resume_id,
            "conversation_id": conversation_id,
            "sender": sender,
            "message": message,
            "message_type": message_type
        }

        return await self.create(CandidateChatHistory, message_data)

    async def batch_create_messages(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[CandidateChatHistory]:
        """
        批量创建消息

        Args:
            messages: 消息列表，每个消息包含tenant_id, resume_id, sender, message等字段

        Returns:
            创建的消息对象列表
        """
        message_objects = [
            CandidateChatHistory(**msg_data)
            for msg_data in messages
        ]

        self.db.add_all(message_objects)
        await self.db.commit()

        for msg in message_objects:
            await self.db.refresh(msg)

        return message_objects

    async def get_latest_messages(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        limit: int = 10
    ) -> List[CandidateChatHistory]:
        """
        获取最新的N条消息（倒序）

        Args:
            conversation_id: 会话ID
            tenant_id: 租户ID
            limit: 返回条数（默认10）

        Returns:
            最新消息列表（时间倒序）
        """
        conditions = [
            CandidateChatHistory.conversation_id == conversation_id,
            CandidateChatHistory.tenant_id == tenant_id
        ]

        query = (
            select(CandidateChatHistory)
            .where(and_(*conditions))
            .order_by(desc(CandidateChatHistory.created_at))
            .limit(limit)
        )

        async with get_db_context() as session:
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_message_count(
        self,
        conversation_id: UUID,
        tenant_id: UUID
    ) -> int:
        """
        获取会话的消息总数

        Args:
            conversation_id: 会话ID
            tenant_id: 租户ID

        Returns:
            消息总数
        """
        from sqlalchemy import func

        conditions = [
            CandidateChatHistory.conversation_id == conversation_id,
            CandidateChatHistory.tenant_id == tenant_id
        ]

        query = select(func.count(CandidateChatHistory.id)).where(and_(*conditions))
        async with get_db_context() as session:
            result = await session.execute(query)
            return result.scalar() or 0
