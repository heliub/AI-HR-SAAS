"""
Conversation Question Tracking service for handling conversation question tracking-related database operations
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, func
from sqlalchemy.orm import joinedload

from app.models.conversation_question_tracking import ConversationQuestionTracking
from app.models.job_question import JobQuestion
from app.services.base_service import BaseService


class ConversationQuestionTrackingService(BaseService):
    """会话问题跟踪服务类，处理会话问题跟踪相关的数据库操作"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_questions_by_conversation(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> List[ConversationQuestionTracking]:
        """根据会话ID获取问题跟踪列表"""
        conditions = [
            ConversationQuestionTracking.conversation_id == conversation_id,
            ConversationQuestionTracking.tenant_id == tenant_id,
            ConversationQuestionTracking.status != "deleted"
        ]

        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(ConversationQuestionTracking.user_id == user_id)

        query = select(ConversationQuestionTracking).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_next_pending_question(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> Optional[ConversationQuestionTracking]:
        """
        获取下一个待处理的问题（性能优化版）

        直接在SQL层过滤pending状态并按sort_order排序，避免查询所有问题后在Python层过滤

        Args:
            conversation_id: 会话ID
            tenant_id: 租户ID
            user_id: 用户ID（可选）
            is_admin: 是否管理员

        Returns:
            下一个待处理的问题，如果没有则返回None
        """
        conditions = [
            ConversationQuestionTracking.conversation_id == conversation_id,
            ConversationQuestionTracking.tenant_id == tenant_id,
            ConversationQuestionTracking.status == "pending"  # 直接SQL过滤
        ]

        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(ConversationQuestionTracking.user_id == user_id)

        # JOIN job_questions表以获取sort_order进行排序
        query = (
            select(ConversationQuestionTracking)
            .join(
                JobQuestion,
                ConversationQuestionTracking.question_id == JobQuestion.id
            )
            .where(and_(*conditions))
            .order_by(JobQuestion.sort_order.asc())  # 按原始问题的排序
            .limit(1)  # 只取第一个
        )

        result = await self.db.execute(query)
        return result.scalar()

    async def create_question_tracking(
        self,
        conversation_id: UUID,
        question_id: UUID,
        job_id: UUID,
        resume_id: UUID,
        question: str,
        tenant_id: UUID,
        user_id: UUID,
        tracking_data: Dict[str, Any] = None
    ) -> ConversationQuestionTracking:
        """创建新问题跟踪记录"""
        if tracking_data is None:
            tracking_data = {}

        # 添加必要字段
        tracking_data.update({
            "conversation_id": conversation_id,
            "question_id": question_id,
            "job_id": job_id,
            "resume_id": resume_id,
            "question": question,
            "tenant_id": tenant_id,
            "user_id": user_id
        })

        return await self.create(ConversationQuestionTracking, tracking_data)

    async def update_question_status(
        self,
        tracking_id: UUID,
        tenant_id: UUID,
        status: str,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> Optional[ConversationQuestionTracking]:
        """更新问题状态"""
        conditions = [
            ConversationQuestionTracking.id == tracking_id,
            ConversationQuestionTracking.tenant_id == tenant_id,
            ConversationQuestionTracking.status != "deleted"
        ]

        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(ConversationQuestionTracking.user_id == user_id)

        query = select(ConversationQuestionTracking).where(and_(*conditions))
        result = await self.db.execute(query)
        db_obj = result.scalar()

        if db_obj:
            db_obj.status = status
            await self.db.commit()
            await self.db.refresh(db_obj)

        return db_obj

    async def update_question_satisfaction(
        self,
        tracking_id: UUID,
        tenant_id: UUID,
        is_satisfied: bool,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> Optional[ConversationQuestionTracking]:
        """更新问题满足状态"""
        conditions = [
            ConversationQuestionTracking.id == tracking_id,
            ConversationQuestionTracking.tenant_id == tenant_id,
            ConversationQuestionTracking.status != "deleted"
        ]

        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(ConversationQuestionTracking.user_id == user_id)

        query = select(ConversationQuestionTracking).where(and_(*conditions))
        result = await self.db.execute(query)
        db_obj = result.scalar()

        if db_obj:
            db_obj.is_satisfied = is_satisfied
            await self.db.commit()
            await self.db.refresh(db_obj)

        return db_obj

    async def update_question_tracking(
        self,
        tracking_id: UUID,
        tenant_id: UUID,
        tracking_data: Dict[str, Any],
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> Optional[ConversationQuestionTracking]:
        """更新问题跟踪信息"""
        conditions = [
            ConversationQuestionTracking.id == tracking_id,
            ConversationQuestionTracking.tenant_id == tenant_id,
            ConversationQuestionTracking.status != "deleted"
        ]

        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(ConversationQuestionTracking.user_id == user_id)

        query = select(ConversationQuestionTracking).where(and_(*conditions))
        result = await self.db.execute(query)
        db_obj = result.scalar()

        if db_obj:
            for key, value in tracking_data.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            await self.db.commit()
            await self.db.refresh(db_obj)

        return db_obj

    async def delete_question_tracking(
        self,
        tracking_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> bool:
        """删除问题跟踪记录（软删除）"""
        conditions = [
            ConversationQuestionTracking.id == tracking_id,
            ConversationQuestionTracking.tenant_id == tenant_id
        ]

        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(ConversationQuestionTracking.user_id == user_id)

        query = select(ConversationQuestionTracking).where(and_(*conditions))
        result = await self.db.execute(query)
        db_obj = result.scalar()

        if db_obj:
            db_obj.status = "deleted"
            await self.db.commit()
            return True

        return False
