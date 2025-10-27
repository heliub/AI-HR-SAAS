"""
Candidate service for handling candidate-related database operations
"""
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, func

from app.models.candidate import Candidate
from app.models.resume import Resume
from app.models.ai_match_result import AIMatchResult
from app.models.chat_log import ChatMediationLog
from app.services.base_service import BaseService


class CandidateService(BaseService):
    """候选人服务类，处理候选人相关的数据库操作"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_candidate_with_resumes(self, candidate_id: UUID, tenant_id: UUID) -> Optional[Dict]:
        """
        获取候选人及其所有简历

        Args:
            candidate_id: 候选人ID
            tenant_id: 租户ID

        Returns:
            包含候选人和简历信息的字典，如果找不到则返回None
        """
        # 获取候选人基本信息
        candidate = await self.get_by_id(Candidate, candidate_id, tenant_id)
        if not candidate:
            return None

        # 获取候选人的所有简历
        resume_query = select(Resume).where(
            and_(
                Resume.candidate_id == candidate_id,
                Resume.tenant_id == tenant_id
            )
        )
        resume_result = await self.db.execute(resume_query)
        resumes = resume_result.scalars().all()

        return {
            "candidate": candidate,
            "resumes": resumes
        }

    async def get_candidate_with_match_results(self, candidate_id: UUID, tenant_id: UUID) -> Optional[Dict]:
        """
        获取候选人及其AI匹配结果

        Args:
            candidate_id: 候选人ID
            tenant_id: 租户ID

        Returns:
            包含候选人和匹配结果的字典
        """
        candidate = await self.get_by_id(Candidate, candidate_id, tenant_id)
        if not candidate:
            return None

        # 获取AI匹配结果
        match_results_query = select(AIMatchResult).where(
            and_(
                AIMatchResult.candidate_id == candidate_id,
                AIMatchResult.tenant_id == tenant_id
            )
        )
        match_results_result = await self.db.execute(match_results_query)
        match_results = match_results_result.scalars().all()

        return {
            "candidate": candidate,
            "match_results": match_results
        }

    async def get_candidate_with_chat_history(self, candidate_id: UUID, tenant_id: UUID) -> Optional[Dict]:
        """
        获取候选人及其聊天记录

        Args:
            candidate_id: 候选人ID
            tenant_id: 租户ID

        Returns:
            包含候选人和聊天记录的字典
        """
        candidate = await self.get_by_id(Candidate, candidate_id, tenant_id)
        if not candidate:
            return None

        # 获取聊天记录
        chat_logs_query = select(ChatMediationLog).where(
            and_(
                ChatMediationLog.candidate_id == candidate_id,
                ChatMediationLog.tenant_id == tenant_id
            )
        ).order_by(ChatMediationLog.created_at.desc())
        chat_logs_result = await self.db.execute(chat_logs_query)
        chat_logs = chat_logs_result.scalars().all()

        return {
            "candidate": candidate,
            "chat_logs": chat_logs
        }

    async def get_candidate_full_profile(self, candidate_id: UUID, tenant_id: UUID) -> Optional[Dict]:
        """
        获取候选人完整档案信息

        Args:
            candidate_id: 候选人ID
            tenant_id: 租户ID

        Returns:
            包含候选人完整信息的字典
        """
        candidate = await self.get_by_id(Candidate, candidate_id, tenant_id)
        if not candidate:
            return None

        # 并行查询所有关联数据
        resumes_query = select(Resume).where(
            and_(
                Resume.candidate_id == candidate_id,
                Resume.tenant_id == tenant_id
            )
        )
        resumes_result = await self.db.execute(resumes_query)
        resumes = resumes_result.scalars().all()

        match_results_query = select(AIMatchResult).where(
            and_(
                AIMatchResult.candidate_id == candidate_id,
                AIMatchResult.tenant_id == tenant_id
            )
        )
        match_results_result = await self.db.execute(match_results_query)
        match_results = match_results_result.scalars().all()

        chat_logs_query = select(ChatMediationLog).where(
            and_(
                ChatMediationLog.candidate_id == candidate_id,
                ChatMediationLog.tenant_id == tenant_id
            )
        ).order_by(ChatMediationLog.created_at.desc())
        chat_logs_result = await self.db.execute(chat_logs_query)
        chat_logs = chat_logs_result.scalars().all()

        return {
            "candidate": candidate,
            "resumes": resumes,
            "match_results": match_results,
            "chat_logs": chat_logs
        }

    def search_candidates(
        self,
        tenant_id: UUID,
        keyword: Optional[str] = None,
        source: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Candidate]:
        """
        搜索候选人

        Args:
            tenant_id: 租户ID
            keyword: 搜索关键词（搜索姓名、邮箱）
            source: 候选人来源
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            候选人列表
        """
        query = select(Candidate).where(Candidate.tenant_id == tenant_id)

        if source:
            query = query.filter(Candidate.source == source)

        if keyword:
            query = query.filter(
                or_(
                    Candidate.name.ilike(f"%{keyword}%"),
                    Candidate.email.ilike(f"%{keyword}%")
                )
            )

        return query.offset(skip).limit(limit).all()

    async def get_candidates_by_job(self, job_id: UUID, tenant_id: UUID) -> List[Dict]:
        """
        获取应聘特定职位的候选人

        Args:
            job_id: 职位ID
            tenant_id: 租户ID

        Returns:
            候选人及其简历信息列表
        """
        # 通过简历表查找候选人
        resumes_query = select(Resume).where(
            and_(
                Resume.job_id == job_id,
                Resume.tenant_id == tenant_id
            )
        )
        resumes_result = await self.db.execute(resumes_query)
        resumes = resumes_result.scalars().all()

        # 🚨 严重性能问题修复：避免在循环中查询数据库
        # 收集所有需要查询的候选人ID
        candidate_ids = list(set([resume.candidate_id for resume in resumes if resume.candidate_id]))

        candidates_data = []
        if candidate_ids:
            # 批量查询候选人信息
            candidates_query = select(Candidate).where(
                and_(
                    Candidate.id.in_(candidate_ids),
                    Candidate.tenant_id == tenant_id
                )
            )
            candidates_result = await self.db.execute(candidates_query)
            candidates = candidates_result.scalars().all()

            # 构建候选人数据映射
            candidate_map = {str(candidate.id): candidate for candidate in candidates}

            # 批量查询简历信息
            resumes_query = select(Resume).where(
                and_(
                    Resume.candidate_id.in_(candidate_ids),
                    Resume.tenant_id == tenant_id
                )
            )
            resumes_result = await self.db.execute(resumes_query)
            candidate_resumes = resumes_result.scalars().all()

            # 按候选人ID分组简历
            resume_map = {}
            for resume in candidate_resumes:
                candidate_id = str(resume.candidate_id)
                if candidate_id not in resume_map:
                    resume_map[candidate_id] = []
                resume_map[candidate_id].append(resume)

            # 构建最终数据
            for candidate_id in candidate_ids:
                candidate = candidate_map.get(candidate_id)
                if candidate:
                    candidates_data.append({
                        "candidate": candidate,
                        "resumes": resume_map.get(candidate_id, [])
                    })

        return candidates_data

    async def create_candidate(self, tenant_id: UUID, candidate_data: Dict) -> Candidate:
        """
        创建新候选人

        Args:
            tenant_id: 租户ID
            candidate_data: 候选人数据

        Returns:
            创建的候选人对象
        """
        candidate_data["tenant_id"] = tenant_id
        return await self.create(Candidate, candidate_data)

    async def update_candidate(self, candidate_id: UUID, tenant_id: UUID, candidate_data: Dict) -> Optional[Candidate]:
        """
        更新候选人信息

        Args:
            candidate_id: 候选人ID
            tenant_id: 租户ID
            candidate_data: 更新的候选人数据

        Returns:
            更新后的候选人对象
        """
        return await self.update(Candidate, candidate_id, candidate_data, tenant_id)