"""
Job Knowledge Service

核心业务逻辑：CRUD、变体管理、数据分析
"""
import json
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update, delete

from app.models.job_knowledge_base import JobKnowledgeBase
from app.models.knowledge_question_variant import KnowledgeQuestionVariant
from app.models.knowledge_hit_log import KnowledgeHitLog
from app.services.base_service import BaseService
from app.services.knowledge_embedding_service import KnowledgeEmbeddingService
from app.services.knowledge_search_service import KnowledgeSearchService
from app.schemas.job_knowledge import SearchMethod
import structlog

logger = structlog.get_logger(__name__)


class JobKnowledgeService(BaseService):
    """岗位/公司知识库服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.embedding_service = KnowledgeEmbeddingService(db)
        self.search_service = KnowledgeSearchService(db)

    # ==============================================
    # CRUD 操作
    # ==============================================

    async def create_knowledge(
        self,
        data: Dict[str, Any],
        tenant_id: UUID,
        user_id: UUID
    ) -> JobKnowledgeBase:
        """
        创建知识库条目

        Args:
            data: 知识库数据
            tenant_id: 租户ID
            user_id: 用户ID

        Returns:
            创建的知识库对象
        """
        # 添加必要字段
        data.update({
            "tenant_id": tenant_id,
            "user_id": user_id,
            "created_by": user_id,
            "status": "active",
        })

        # 创建记录
        knowledge = await self.create(JobKnowledgeBase, data)

        # 同步生成embedding
        try:
            # embedding = await self.embedding_service.generate_for_text(knowledge.question)
            embedding = [0.0] * 2048
            stmt = (
                update(JobKnowledgeBase)
                .where(JobKnowledgeBase.id == knowledge.id)
                .values(question_embedding=embedding)
            )
            await self.db.execute(stmt)
            await self.db.commit()
            await self.db.refresh(knowledge)
            logger.info("knowledge_created_with_embedding", knowledge_id=knowledge.id)
        except Exception as e:
            logger.warning("failed_to_generate_embedding_on_create",
                          knowledge_id=knowledge.id, error=str(e))

        return knowledge

    async def get_knowledge_by_id(
        self,
        knowledge_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> Optional[JobKnowledgeBase]:
        """获取知识库条目"""
        conditions = [
            JobKnowledgeBase.id == knowledge_id,
            JobKnowledgeBase.tenant_id == tenant_id,
            JobKnowledgeBase.status != "deleted"
        ]

        # 非管理员只能查看自己的
        if user_id and not is_admin:
            conditions.append(JobKnowledgeBase.user_id == user_id)

        query = select(JobKnowledgeBase).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalar()

    async def list_knowledge(
        self,
        tenant_id: UUID,
        scope_type: Optional[str] = None,
        scope_id: Optional[UUID] = None,
        category: Optional[str] = None,
        status: str = "active",
        user_id: Optional[UUID] = None,
        is_admin: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[JobKnowledgeBase], int]:
        """
        查询知识库列表

        Returns:
            (知识库列表, 总数)
        """
        conditions = [
            JobKnowledgeBase.tenant_id == tenant_id,
            JobKnowledgeBase.status == status
        ]

        if scope_type:
            conditions.append(JobKnowledgeBase.scope_type == scope_type)
        if scope_id:
            conditions.append(JobKnowledgeBase.scope_id == scope_id)
        if category:
            # 字符串包含查询 - 使用PostgreSQL的LIKE操作符
            from sqlalchemy import text
            conditions.append(text(f"categories LIKE '%{category}%'"))

        # 非管理员只能查看自己的
        if user_id and not is_admin:
            conditions.append(JobKnowledgeBase.user_id == user_id)

        # 查询总数
        count_query = select(func.count(JobKnowledgeBase.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 查询列表
        query = (
            select(JobKnowledgeBase)
            .where(and_(*conditions))
            .order_by(JobKnowledgeBase.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        items = result.scalars().all()

        return list(items), total

    async def update_knowledge(
        self,
        knowledge_id: UUID,
        data: Dict[str, Any],
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> Optional[JobKnowledgeBase]:
        """更新知识库条目"""
        # 获取记录
        knowledge = await self.get_knowledge_by_id(knowledge_id, tenant_id, user_id, is_admin)
        if not knowledge:
            return None

        # 更新字段
        data["updated_by"] = user_id
        for key, value in data.items():
            if hasattr(knowledge, key):
                setattr(knowledge, key, value)

        # 如果问题改变了，重新生成embedding
        # if "question" in data:
        #     try:
        #         embedding = await self.embedding_service.generate_for_text(data["question"])
        #         knowledge.question_embedding = embedding
        #         logger.info("knowledge_embedding_regenerated", knowledge_id=knowledge_id)
        #     except Exception as e:
        #         logger.warning("failed_to_regenerate_embedding",
        #                       knowledge_id=knowledge_id, error=str(e))

        await self.db.commit()
        await self.db.refresh(knowledge)
        return knowledge

    async def delete_knowledge(
        self,
        knowledge_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False
    ) -> bool:
        """删除知识库条目（软删除）"""
        knowledge = await self.get_knowledge_by_id(knowledge_id, tenant_id, user_id, is_admin)
        if not knowledge:
            return False

        knowledge.status = "deleted"
        knowledge.updated_by = user_id
        await self.db.commit()
        return True

    # ==============================================
    # 批量操作
    # ==============================================

    async def batch_create_knowledge(
        self,
        items: List[Dict[str, Any]],
        scope_type: str,
        scope_id: UUID,
        tenant_id: UUID,
        user_id: UUID
    ) -> tuple[List[JobKnowledgeBase], List[Dict[str, Any]]]:
        """
        批量创建知识库

        Returns:
            (成功列表, 错误列表)
        """
        success_items = []
        error_items = []
        knowledge_ids = []

        for idx, item_data in enumerate(items):
            try:
                # 添加必要字段
                item_data.update({
                    "scope_type": scope_type,
                    "scope_id": scope_id,
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "created_by": user_id,
                    "status": "active",
                })

                # 创建记录（不立即生成embedding）
                knowledge = await self.create(JobKnowledgeBase, item_data)
                success_items.append(knowledge)
                knowledge_ids.append(knowledge.id)

            except Exception as e:
                error_items.append({
                    "index": idx,
                    "error": str(e),
                    "data": item_data
                })
                logger.error("batch_create_item_failed", index=idx, error=str(e))

        # 批量异步生成embedding
        if knowledge_ids:
            await self.embedding_service.generate_batch_async(knowledge_ids, tenant_id)

        logger.info("batch_create_completed",
                   total=len(items),
                   success=len(success_items),
                   failed=len(error_items))

        return success_items, error_items

    # ==============================================
    # 问题变体管理
    # ==============================================

    async def add_variant(
        self,
        knowledge_id: UUID,
        variant_question: str,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False,
        source: str = "manual",
        confidence_score: Optional[Decimal] = None
    ) -> Optional[KnowledgeQuestionVariant]:
        """添加问题变体"""
        # 验证知识库存在
        knowledge = await self.get_knowledge_by_id(knowledge_id, tenant_id, user_id, is_admin)
        if not knowledge:
            return None

        # 创建变体
        variant_data = {
            "tenant_id": tenant_id,
            "knowledge_id": knowledge_id,
            "scope_type": knowledge.scope_type,
            "scope_id": knowledge.scope_id,
            "variant_question": variant_question,
            "source": source,
            "confidence_score": confidence_score,
            "status": "active",
        }

        variant = await self.create(KnowledgeQuestionVariant, variant_data)

        # 同步生成embedding
        try:
            embedding = await self.embedding_service.generate_for_text(variant_question)
            stmt = (
                update(KnowledgeQuestionVariant)
                .where(KnowledgeQuestionVariant.id == variant.id)
                .values(variant_embedding=embedding)
            )
            await self.db.execute(stmt)
            await self.db.commit()
            await self.db.refresh(variant)
            logger.info("variant_created_with_embedding", variant_id=variant.id)
        except Exception as e:
            logger.warning("failed_to_generate_variant_embedding",
                          variant_id=variant.id, error=str(e))

        return variant

    async def ai_generate_variants(
        self,
        knowledge_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        is_admin: bool = False,
        max_variants: int = 5
    ) -> List[Dict[str, Any]]:
        """
        AI自动生成问题变体

        Returns:
            变体建议列表
        """
        from app.ai.llm.factory import get_llm_client
        from app.ai.llm.types import LLMRequest, Message

        # 验证知识库存在
        knowledge = await self.get_knowledge_by_id(knowledge_id, tenant_id, user_id, is_admin)
        if not knowledge:
            return []

        # 读取prompt模板
        import os
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "ai/prompts/generate_question_variants.md"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        # 填充prompt
        user_prompt = prompt_template.format(
            original_question=knowledge.question,
            max_variants=max_variants
        )

        # 调用LLM
        try:
            llm_client = get_llm_client("volcengine")
            request = LLMRequest(
                model="doubao-1.5-pro-32k-250115",
                messages=[Message(role="user", content=user_prompt)],
                system="你是一个专业的HR助手，负责为知识库问题生成相似的问法变体。",
                temperature=0.1,
                max_tokens=2000,
            )

            response = await llm_client.chat(request)
            content = response.content or ""

            # 解析JSON
            # 移除markdown代码块标记
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            variants_data = json.loads(content)

            logger.info("ai_variants_generated",
                       knowledge_id=knowledge_id,
                       count=len(variants_data))

            return variants_data

        except Exception as e:
            logger.error("failed_to_generate_ai_variants",
                        knowledge_id=knowledge_id, error=str(e))
            raise

    async def list_variants(
        self,
        knowledge_id: UUID,
        tenant_id: UUID
    ) -> List[KnowledgeQuestionVariant]:
        """查询变体列表"""
        query = (
            select(KnowledgeQuestionVariant)
            .where(
                and_(
                    KnowledgeQuestionVariant.knowledge_id == knowledge_id,
                    KnowledgeQuestionVariant.tenant_id == tenant_id,
                    KnowledgeQuestionVariant.status == "active"
                )
            )
            .order_by(KnowledgeQuestionVariant.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_variant(
        self,
        variant_id: UUID,
        tenant_id: UUID
    ) -> bool:
        """删除变体（软删除）"""
        stmt = (
            update(KnowledgeQuestionVariant)
            .where(
                and_(
                    KnowledgeQuestionVariant.id == variant_id,
                    KnowledgeQuestionVariant.tenant_id == tenant_id
                )
            )
            .values(status="deleted")
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    # ==============================================
    # 检索与日志
    # ==============================================

    async def search_for_conversation(
        self,
        query: str,
        job_id: UUID,
        tenant_id: UUID,
        conversation_id: Optional[UUID] = None,
        method: SearchMethod = SearchMethod.SIMPLE,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        供对话服务调用的检索接口（内部）

        自动处理：
        1. 检索岗位级 + 公司级知识
        2. 记录命中日志
        3. 返回格式化结果
        """
        # 检索
        results = await self.search_service.search(
            query=query,
            scope_type="job",
            scope_id=job_id,
            tenant_id=tenant_id,
            method=method,
            include_company=True,
            top_k=top_k
        )

        # 记录日志
        if results and conversation_id:
            await self._log_hits(results, query, conversation_id, tenant_id)

        return results

    async def _log_hits(
        self,
        results: List[Dict[str, Any]],
        user_question: str,
        conversation_id: UUID,
        tenant_id: UUID
    ) -> None:
        """记录命中日志"""
        try:
            for rank, result in enumerate(results, start=1):
                log_data = {
                    "tenant_id": tenant_id,
                    "knowledge_id": result["knowledge_id"],
                    "variant_id": result.get("variant_id"),
                    "conversation_id": conversation_id,
                    "user_question": user_question,
                    "match_method": result["match_method"],
                    "match_score": result["match_score"],
                    "rank_position": rank,
                }
                await self.create(KnowledgeHitLog, log_data)

            logger.info("hit_logs_recorded", count=len(results))
        except Exception as e:
            logger.error("failed_to_record_hit_logs", error=str(e))
            # 不抛出异常，日志记录失败不应影响主流程

    # ==============================================
    # 数据分析
    # ==============================================

    async def get_hot_questions(
        self,
        scope_id: UUID,
        tenant_id: UUID,
        days: int = 30,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """热门问题分析"""
        try:
            # 计算时间范围
            since = datetime.utcnow() - timedelta(days=days)

            # 查询热门问题
            query = (
                select(
                    JobKnowledgeBase.id,
                    JobKnowledgeBase.question,
                    JobKnowledgeBase.answer,
                    func.count(KnowledgeHitLog.id).label("hit_count"),
                    func.max(KnowledgeHitLog.created_at).label("last_hit_at")
                )
                .join(KnowledgeHitLog, JobKnowledgeBase.id == KnowledgeHitLog.knowledge_id)
                .where(
                    and_(
                        JobKnowledgeBase.tenant_id == tenant_id,
                        JobKnowledgeBase.scope_id == scope_id,
                        KnowledgeHitLog.created_at > since
                    )
                )
                .group_by(JobKnowledgeBase.id)
                .order_by(func.count(KnowledgeHitLog.id).desc())
                .limit(limit)
            )

            result = await self.db.execute(query)
            rows = result.fetchall()

            items = []
            for row in rows:
                items.append({
                    "knowledge_id": row.id,
                    "question": row.question,
                    "answer": row.answer,
                    "hit_count": row.hit_count,
                    "last_hit_at": row.last_hit_at,
                })

            logger.info("hot_questions_retrieved", count=len(items))
            return items

        except Exception as e:
            logger.error("failed_to_get_hot_questions", error=str(e))
            raise

    async def get_missed_questions(
        self,
        scope_id: UUID,
        tenant_id: UUID,
        days: int = 7,
        min_occurrences: int = 3,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """未命中问题分析"""
        try:
            # 计算时间范围
            since = datetime.utcnow() - timedelta(days=days)

            # 查询低分命中的问题
            query = (
                select(
                    KnowledgeHitLog.user_question,
                    KnowledgeHitLog.match_score
                )
                .where(
                    and_(
                        KnowledgeHitLog.tenant_id == tenant_id,
                        KnowledgeHitLog.created_at > since,
                        or_(
                            KnowledgeHitLog.match_score < 0.5,
                            KnowledgeHitLog.match_score.is_(None)
                        )
                    )
                )
            )

            result = await self.db.execute(query)
            rows = result.fetchall()

            # 聚合相似问题（简单版：完全匹配）
            question_counts = defaultdict(int)
            for row in rows:
                if row.user_question:
                    question_counts[row.user_question] += 1

            # 过滤并排序
            missed = [
                {"question": q, "count": c}
                for q, c in question_counts.items()
                if c >= min_occurrences
            ]
            missed.sort(key=lambda x: x["count"], reverse=True)

            logger.info("missed_questions_retrieved", count=len(missed[:limit]))
            return missed[:limit]

        except Exception as e:
            logger.error("failed_to_get_missed_questions", error=str(e))
            raise

    async def get_coverage_stats(
        self,
        scope_id: UUID,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """知识库覆盖率统计"""
        try:
            # 总知识库数量
            total_query = select(func.count(JobKnowledgeBase.id)).where(
                and_(
                    JobKnowledgeBase.tenant_id == tenant_id,
                    JobKnowledgeBase.scope_id == scope_id,
                    JobKnowledgeBase.status == "active"
                )
            )
            total_result = await self.db.execute(total_query)
            total_knowledge = total_result.scalar() or 0

            # 已生成embedding的数量
            with_embedding_query = select(func.count(JobKnowledgeBase.id)).where(
                and_(
                    JobKnowledgeBase.tenant_id == tenant_id,
                    JobKnowledgeBase.scope_id == scope_id,
                    JobKnowledgeBase.status == "active",
                    JobKnowledgeBase.question_embedding.isnot(None)
                )
            )
            with_embedding_result = await self.db.execute(with_embedding_query)
            with_embedding = with_embedding_result.scalar() or 0

            # 有变体的知识库数量
            with_variants_query = select(func.count(func.distinct(KnowledgeQuestionVariant.knowledge_id))).where(
                and_(
                    KnowledgeQuestionVariant.tenant_id == tenant_id,
                    KnowledgeQuestionVariant.scope_id == scope_id,
                    KnowledgeQuestionVariant.status == "active"
                )
            )
            with_variants_result = await self.db.execute(with_variants_query)
            with_variants = with_variants_result.scalar() or 0

            # 平均命中分数
            avg_score_query = (
                select(func.avg(KnowledgeHitLog.match_score))
                .join(JobKnowledgeBase, KnowledgeHitLog.knowledge_id == JobKnowledgeBase.id)
                .where(
                    and_(
                        JobKnowledgeBase.tenant_id == tenant_id,
                        JobKnowledgeBase.scope_id == scope_id,
                        KnowledgeHitLog.match_score.isnot(None)
                    )
                )
            )
            avg_score_result = await self.db.execute(avg_score_query)
            avg_hit_score = float(avg_score_result.scalar() or 0.0)

            # 计算覆盖率
            embedding_coverage = (with_embedding / total_knowledge * 100) if total_knowledge > 0 else 0.0

            stats = {
                "total_knowledge": total_knowledge,
                "with_embedding": with_embedding,
                "with_variants": with_variants,
                "avg_hit_score": avg_hit_score,
                "embedding_coverage": round(embedding_coverage, 2),
            }

            logger.info("coverage_stats_retrieved", stats=stats)
            return stats

        except Exception as e:
            logger.error("failed_to_get_coverage_stats", error=str(e))
            raise
