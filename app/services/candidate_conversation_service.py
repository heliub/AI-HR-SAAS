"""
Candidate Conversation service for handling candidate conversation-related database operations
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, func

from app.models.candidate_conversation import CandidateConversation
from app.services.base_service import BaseService


class CandidateConversationService(BaseService):
    """候选人会话服务类，处理候选人会话相关的数据库操作"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_conversation_by_id(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> Optional[CandidateConversation]:
        """根据会话ID获取会话详情"""
        conditions = [
            CandidateConversation.id == conversation_id,
            CandidateConversation.tenant_id == tenant_id,
            CandidateConversation.status != "deleted"
        ]

        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(CandidateConversation.user_id == user_id)

        query = select(CandidateConversation).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalar()

    async def get_conversation_by_job_and_resume(
        self,
        job_id: UUID,
        resume_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> Optional[CandidateConversation]:
        """根据职位ID和简历ID获取会话详情"""
        conditions = [
            CandidateConversation.job_id == job_id,
            CandidateConversation.resume_id == resume_id,
            CandidateConversation.tenant_id == tenant_id,
            CandidateConversation.status != "deleted"
        ]

        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(CandidateConversation.user_id == user_id)

        query = select(CandidateConversation).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalar()

    async def create_conversation(
        self,
        tenant_id: UUID,
        user_id: UUID,
        resume_id: UUID,
        job_id: UUID,
        conversation_data: Dict[str, Any] = None
    ) -> CandidateConversation:
        """创建新会话"""
        if conversation_data is None:
            conversation_data = {}

        # 添加必要字段
        conversation_data.update({
            "tenant_id": tenant_id,
            "user_id": user_id,
            "resume_id": resume_id,
            "job_id": job_id
        })

        return await self.create(CandidateConversation, conversation_data)

    async def update_conversation_status(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        status: str,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> Optional[CandidateConversation]:
        """更新会话状态"""
        conditions = [
            CandidateConversation.id == conversation_id,
            CandidateConversation.tenant_id == tenant_id,
            CandidateConversation.status != "deleted"
        ]

        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(CandidateConversation.user_id == user_id)

        query = select(CandidateConversation).where(and_(*conditions))
        result = await self.db.execute(query)
        db_obj = result.scalar()

        if db_obj:
            db_obj.status = status
            await self.db.commit()
            await self.db.refresh(db_obj)

        return db_obj

    async def update_conversation_stage(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        stage: str,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> Optional[CandidateConversation]:
        """更新会话阶段"""
        conditions = [
            CandidateConversation.id == conversation_id,
            CandidateConversation.tenant_id == tenant_id,
            CandidateConversation.status != "deleted"
        ]

        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(CandidateConversation.user_id == user_id)

        query = select(CandidateConversation).where(and_(*conditions))
        result = await self.db.execute(query)
        db_obj = result.scalar()

        if db_obj:
            db_obj.stage = stage
            await self.db.commit()
            await self.db.refresh(db_obj)

        return db_obj

    async def update_conversation_summary(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        summary: str,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> Optional[CandidateConversation]:
        """更新会话摘要"""
        conditions = [
            CandidateConversation.id == conversation_id,
            CandidateConversation.tenant_id == tenant_id,
            CandidateConversation.status != "deleted"
        ]

        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(CandidateConversation.user_id == user_id)

        query = select(CandidateConversation).where(and_(*conditions))
        result = await self.db.execute(query)
        db_obj = result.scalar()

        if db_obj:
            db_obj.summary = summary
            await self.db.commit()
            await self.db.refresh(db_obj)

        return db_obj

    async def update_conversation(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        conversation_data: Dict[str, Any],
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> Optional[CandidateConversation]:
        """更新会话信息"""
        conditions = [
            CandidateConversation.id == conversation_id,
            CandidateConversation.tenant_id == tenant_id,
            CandidateConversation.status != "deleted"
        ]

        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(CandidateConversation.user_id == user_id)

        query = select(CandidateConversation).where(and_(*conditions))
        result = await self.db.execute(query)
        db_obj = result.scalar()

        if db_obj:
            for key, value in conversation_data.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            await self.db.commit()
            await self.db.refresh(db_obj)

        return db_obj

    async def delete_conversation(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> bool:
        """删除会话（软删除）"""
        conditions = [
            CandidateConversation.id == conversation_id,
            CandidateConversation.tenant_id == tenant_id
        ]

        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(CandidateConversation.user_id == user_id)

        query = select(CandidateConversation).where(and_(*conditions))
        result = await self.db.execute(query)
        db_obj = result.scalar()

        if db_obj:
            db_obj.status = "deleted"
            await self.db.commit()
            return True

        return False
