"""
Job Question service for handling job question-related database operations
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, func

from app.models.job_question import JobQuestion
from app.services.base_service import BaseService
from app.infrastructure.database.session import get_db_context


class JobQuestionService(BaseService):
    """职位问题服务类，处理职位问题相关的数据库操作"""

    def __init__(self, db: Optional[AsyncSession] = None):
        super().__init__(db)

    async def get_questions_by_job(
        self,
        job_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> List[JobQuestion]:
        """根据职位ID获取问题列表"""
        conditions = [
            JobQuestion.job_id == job_id,
            JobQuestion.tenant_id == tenant_id,
            JobQuestion.status != "deleted"
        ]

        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(JobQuestion.user_id == user_id)

        query = select(JobQuestion).where(and_(*conditions)).order_by(JobQuestion.sort_order)
        async with get_db_context() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def create_question(
        self,
        job_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
        question_data: Dict[str, Any]
    ) -> JobQuestion:
        """创建新问题"""
        # 添加必要字段
        question_data.update({
            "job_id": job_id,
            "tenant_id": tenant_id,
            "user_id": user_id
        })
        
        # 如果没有指定排序，设置为当前最大排序+1
        if "sort_order" not in question_data:
            max_sort_query = select(func.coalesce(func.max(JobQuestion.sort_order), 0)).where(
                and_(
                    JobQuestion.job_id == job_id,
                    JobQuestion.tenant_id == tenant_id,
                    JobQuestion.status != "deleted"
                )
            )
            max_sort_result = await self.db.execute(max_sort_query)
            max_sort = max_sort_result.scalar() or 0
            question_data["sort_order"] = max_sort + 1

        return await self.create(JobQuestion, question_data)

    async def update_question(
        self,
        question_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False,
        question_data: Dict[str, Any] = None
    ) -> Optional[JobQuestion]:
        """更新问题"""
        if question_data is None:
            question_data = {}

        # 获取问题
        conditions = [JobQuestion.id == question_id, JobQuestion.tenant_id == tenant_id]
        
        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(JobQuestion.user_id == user_id)

        query = select(JobQuestion).where(and_(*conditions))
        result = await self.db.execute(query)
        db_obj = result.scalar()
        
        if db_obj:
            for key, value in question_data.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            await self.db.commit()
            await self.db.refresh(db_obj)
        
        return db_obj

    async def delete_question(
        self,
        question_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> bool:
        """删除问题（软删除）"""
        # 获取问题
        conditions = [JobQuestion.id == question_id, JobQuestion.tenant_id == tenant_id]
        
        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(JobQuestion.user_id == user_id)

        query = select(JobQuestion).where(and_(*conditions))
        result = await self.db.execute(query)
        db_obj = result.scalar()
        
        if db_obj:
            db_obj.status = "deleted"
            await self.db.commit()
            return True
        
        return False

    async def reorder_questions(
        self,
        job_id: UUID,
        tenant_id: UUID,
        question_orders: List[Dict[str, Any]],
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> bool:
        """重新排序问题"""
        # 验证权限
        conditions = [
            JobQuestion.job_id == job_id,
            JobQuestion.tenant_id == tenant_id,
            JobQuestion.status != "deleted"
        ]
        
        # 用户过滤 - 只有非管理员时才过滤
        if user_id and not is_admin:
            conditions.append(JobQuestion.user_id == user_id)

        query = select(JobQuestion).where(and_(*conditions))
        result = await self.db.execute(query)
        questions = result.scalars().all()
        
        # 创建问题ID到对象的映射
        question_map = {str(q.id): q for q in questions}
        
        # 更新排序
        for order_data in question_orders:
            question_id = order_data.get("question_id")
            sort_order = order_data.get("sort_order")
            
            if question_id in question_map:
                question_map[question_id].sort_order = sort_order
        
        await self.db.commit()
        return True
