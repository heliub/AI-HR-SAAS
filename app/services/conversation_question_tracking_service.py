"""
Conversation Question Tracking service for handling conversation question tracking-related database operations
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, update, case
from sqlalchemy.orm import joinedload

from app.models.conversation_question_tracking import ConversationQuestionTracking
from app.models.job_question import JobQuestion
from app.services.base_service import BaseService
from app.infrastructure.database.session import get_db_context


class ConversationQuestionTrackingService(BaseService):
    """会话问题跟踪服务类，处理会话问题跟踪相关的数据库操作"""

    def __init__(self, db: Optional[AsyncSession] = None):
        super().__init__(db)

    async def get_questions_by_conversation(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False,
        status: Optional[str] = None
    ) -> List[ConversationQuestionTracking]:
        """根据会话ID获取问题跟踪列表"""
        conditions = [
            ConversationQuestionTracking.conversation_id == conversation_id,
            ConversationQuestionTracking.tenant_id == tenant_id,
            ConversationQuestionTracking.status != "deleted"
        ]

        # 状态过滤
        if status:
            conditions.append(ConversationQuestionTracking.status == status)

        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(ConversationQuestionTracking.user_id == user_id)

        query = select(ConversationQuestionTracking).where(and_(*conditions))   
        async with get_db_context() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def get_next_question(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> Optional[ConversationQuestionTracking]:
        """
        获取下一个问题（优先进行中，其次待处理）
        
        使用单个SQL查询，优先返回ongoing状态的问题，其次返回pending状态的问题
        
        Args:
            conversation_id: 会话ID
            tenant_id: 租户ID
            user_id: 用户ID（可选）
            is_admin: 是否管理员
        
        Returns:
            下一个问题，如果没有则返回None
        """
        # 基础查询条件
        conditions = [
            ConversationQuestionTracking.conversation_id == conversation_id,
            ConversationQuestionTracking.tenant_id == tenant_id,
            ConversationQuestionTracking.status.in_(["ongoing", "pending"])  # 只查询进行中和待处理状态
        ]
        
        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(ConversationQuestionTracking.user_id == user_id)
        
        priority_order = case(
            (
                ConversationQuestionTracking.status == "ongoing", 0
            ),
            (
                ConversationQuestionTracking.status == "pending", 1
            ),
            else_=2
        )
        
        query = (
            select(ConversationQuestionTracking)
            .join(
                JobQuestion,
                ConversationQuestionTracking.question_id == JobQuestion.id
            )
            .where(and_(*conditions))
            .order_by(
                priority_order,  # 优先级排序：ongoing(0) < pending(1)
                JobQuestion.sort_order.asc()  # 相同状态下按原始问题的排序
            )
            .limit(1)  # 只取第一个
        )
        
        async with get_db_context() as session:
            result = await session.execute(query)
            return result.scalar_one_or_none()

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

        async with get_db_context() as session:
            result = await session.execute(query)
            return result.scalar_one_or_none()

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

    async def bulk_create_question_tracking(
        self,
        conversation_id: UUID,
        job_id: UUID,
        resume_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
        job_questions: List[JobQuestion]
    ) -> None:
        """
        批量创建问题跟踪记录（不返回结果，提高性能）
        
        Args:
            conversation_id: 会话ID
            job_id: 职位ID
            resume_id: 简历ID
            tenant_id: 租户ID
            user_id: 用户ID
            job_questions: 职位问题列表
        """
        tracking_records = []
        
        # 准备所有要插入的记录
        for question in job_questions:
            tracking_data = {
                "conversation_id": conversation_id,
                "question_id": question.id,
                "job_id": job_id,
                "resume_id": resume_id,
                "question": question.question,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "status": "pending"
            }
            tracking_records.append(ConversationQuestionTracking(**tracking_data))
        
        # 批量插入
        async with get_db_context() as session:
            session.add_all(tracking_records)


    async def update_question_status(
        self,
        tracking_id: UUID,
        tenant_id: UUID,
        status: str,
        user_id: Optional[UUID] = None,
        is_admin: bool = False,
        is_satisfied: Optional[bool] = None
    ) -> Optional[ConversationQuestionTracking]:
        conditions = [ConversationQuestionTracking.id == tracking_id, ConversationQuestionTracking.tenant_id == tenant_id, ConversationQuestionTracking.status != "deleted"]
        if user_id and not is_admin:
            conditions.append(ConversationQuestionTracking.user_id == user_id)
        async with get_db_context() as session:
            stmt = update(ConversationQuestionTracking).where(and_(*conditions)).values(status=status, is_satisfied=is_satisfied).returning(ConversationQuestionTracking)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

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
