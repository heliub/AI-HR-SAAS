"""
Candidate Conversation service for handling candidate conversation-related database operations
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, select, func

from app.models.candidate_conversation import CandidateConversation
from app.services.base_service import BaseService
from app.infrastructure.database.session import get_db_context
from sqlalchemy import update

class CandidateConversationService(BaseService):
    """候选人会话服务类，处理候选人会话相关的数据库操作"""

    def __init__(self):
        """初始化候选人会话服务，不再需要传入db参数"""
        super().__init__()

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
            
        async with get_db_context() as session:
            query = select(CandidateConversation).where(and_(*conditions))
            result = await session.execute(query)
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

        async with get_db_context() as session:
            query = select(CandidateConversation).where(and_(*conditions))
            result = await session.execute(query)
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

        async with get_db_context() as session:
            db_obj = CandidateConversation(**conversation_data)
            session.add(db_obj)
            await session.flush()  # 确保对象被分配ID
            await session.refresh(db_obj)
            return db_obj

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

        async with get_db_context() as session:
            # 构建更新语句
            stmt = update(CandidateConversation).where(and_(*conditions)).values(status=status).returning(CandidateConversation)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

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

        async with get_db_context() as session:
            # 构建更新语句
            stmt = update(CandidateConversation).where(and_(*conditions)).values(stage=stage).returning(CandidateConversation)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

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

        async with get_db_context() as session:
            # 构建更新语句
            stmt = update(CandidateConversation).where(and_(*conditions)).values(summary=summary).returning(CandidateConversation)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

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

        async with get_db_context() as session:
            # 构建更新语句
            stmt = update(CandidateConversation).where(and_(*conditions)).values(**conversation_data).returning(CandidateConversation)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

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

        async with get_db_context() as session:
            # 构建更新语句（软删除）
            stmt = update(CandidateConversation).where(and_(*conditions)).values(status="deleted")
            result = await session.execute(stmt)
            return result.rowcount > 0

    async def get_conversations(
        self,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False,
        status: Optional[str] = None,
        stage: Optional[str] = None,
        resume_id: Optional[UUID] = None,
        job_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[List[CandidateConversation], int]:
        """获取会话列表"""
        conditions = [
            CandidateConversation.tenant_id == tenant_id,
            CandidateConversation.status != "deleted"
        ]

        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(CandidateConversation.user_id == user_id)

        # 状态过滤
        if status:
            conditions.append(CandidateConversation.status == status)

        # 阶段过滤
        if stage:
            conditions.append(CandidateConversation.stage == stage)

        # 简历ID过滤
        if resume_id:
            conditions.append(CandidateConversation.resume_id == resume_id)

        # 职位ID过滤
        if job_id:
            conditions.append(CandidateConversation.job_id == job_id)

        async with get_db_context() as session:
            # 构建查询
            count_query = select(func.count()).select_from(
                select(CandidateConversation).where(and_(*conditions)).subquery()
            )
            count_result = await session.execute(count_query)
            total = count_result.scalar()

            # 获取分页数据
            query = (
                select(CandidateConversation)
                .where(and_(*conditions))
                .order_by(CandidateConversation.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(query)
            conversations = result.scalars().all()

            return list(conversations), total
