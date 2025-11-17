"""
Knowledge Search Service

负责知识库的混合检索（向量+BM25）
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, text, func

from app.models.job_knowledge_base import JobKnowledgeBase
from app.models.knowledge_question_variant import KnowledgeQuestionVariant
from app.services.knowledge_embedding_service import KnowledgeEmbeddingService
from app.schemas.job_knowledge import SearchMethod
import structlog
from app.infrastructure.database.session import get_db_context

logger = structlog.get_logger(__name__)


class KnowledgeSearchService:
    """知识库检索服务（支持向量、BM25、混合检索）"""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.embedding_service = KnowledgeEmbeddingService(db)

    async def search(
        self,
        query: str,
        scope_type: str,
        scope_id: UUID,
        tenant_id: UUID,
        method: SearchMethod = SearchMethod.HYBRID,
        include_company: bool = True,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        统一检索入口

        Args:
            query: 查询文本
            scope_type: 作用域类型
            scope_id: 作用域ID
            tenant_id: 租户ID
            method: 检索方法
            include_company: 是否包含公司级知识
            top_k: 返回Top K结果

        Returns:
            检索结果列表
        """
        logger.info("knowledge_search", query=query, method=method.value, top_k=top_k)

        if method == SearchMethod.VECTOR:
            return await self._vector_search(
                query, scope_type, scope_id, tenant_id, include_company, top_k
            )
        elif method == SearchMethod.BM25:
            return await self._bm25_search(
                query, scope_type, scope_id, tenant_id, include_company, top_k
            )
        elif method == SearchMethod.HYBRID:
            return await self._hybrid_search(
                query, scope_type, scope_id, tenant_id, include_company, top_k
            )
        else:  # SIMPLE
            return await self._simple_filter(
                scope_type, scope_id, tenant_id, include_company, top_k
            )

    async def _vector_search(
        self,
        query: str,
        scope_type: str,
        scope_id: UUID,
        tenant_id: UUID,
        include_company: bool,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        向量检索

        Args:
            query: 查询文本
            scope_type: 作用域类型
            scope_id: 作用域ID
            tenant_id: 租户ID
            include_company: 是否包含公司级知识
            top_k: 返回Top K结果

        Returns:
            检索结果列表
        """
        try:
            # 生成查询embedding
            query_embedding = await self.embedding_service.generate_for_text(query)

            # 构建scope条件
            scope_conditions = []
            if scope_type == "job":
                scope_conditions.append(
                    and_(
                        JobKnowledgeBase.scope_type == "job",
                        JobKnowledgeBase.scope_id == scope_id
                    )
                )
                if include_company:
                    # 同时包含公司级知识
                    scope_conditions.append(
                        and_(
                            JobKnowledgeBase.scope_type == "company",
                            JobKnowledgeBase.scope_id == tenant_id
                        )
                    )
            else:
                scope_conditions.append(
                    and_(
                        JobKnowledgeBase.scope_type == scope_type,
                        JobKnowledgeBase.scope_id == scope_id
                    )
                )

            # 主问题向量检索
            # 使用 PostgreSQL 的向量运算符 <=> (余弦距离)
            main_query = (
                select(
                    JobKnowledgeBase.id,
                    JobKnowledgeBase.question,
                    JobKnowledgeBase.answer,
                    JobKnowledgeBase.categories,
                    JobKnowledgeBase.question_embedding.cosine_distance(query_embedding).label("distance")
                )
                .where(
                    and_(
                        JobKnowledgeBase.tenant_id == tenant_id,
                        or_(*scope_conditions),
                        JobKnowledgeBase.status == "active",
                        JobKnowledgeBase.question_embedding.isnot(None)
                    )
                )
                .order_by(text("distance"))
                .limit(top_k * 2)  # 多取一些，后续合并
            )

            result = await self.db.execute(main_query)
            main_results = result.fetchall()

            # 变体向量检索
            variant_query = (
                select(
                    KnowledgeQuestionVariant.knowledge_id,
                    KnowledgeQuestionVariant.id.label("variant_id"),
                    KnowledgeQuestionVariant.variant_embedding.cosine_distance(query_embedding).label("distance")
                )
                .where(
                    and_(
                        KnowledgeQuestionVariant.tenant_id == tenant_id,
                        or_(
                            and_(
                                KnowledgeQuestionVariant.scope_type == scope_type,
                                KnowledgeQuestionVariant.scope_id == scope_id
                            ),
                            and_(
                                KnowledgeQuestionVariant.scope_type == "company",
                                KnowledgeQuestionVariant.scope_id == tenant_id
                            ) if include_company and scope_type == "job" else False
                        ),
                        KnowledgeQuestionVariant.status == "active",
                        KnowledgeQuestionVariant.variant_embedding.isnot(None)
                    )
                )
                .order_by(text("distance"))
                .limit(top_k * 2)
            )

            variant_result = await self.db.execute(variant_query)
            variant_results = variant_result.fetchall()

            # 获取变体对应的知识库详情
            variant_knowledge_ids = [v.knowledge_id for v in variant_results]
            if variant_knowledge_ids:
                knowledge_query = select(JobKnowledgeBase).where(
                    JobKnowledgeBase.id.in_(variant_knowledge_ids)
                )
                knowledge_result = await self.db.execute(knowledge_query)
                knowledge_map = {k.id: k for k in knowledge_result.scalars().all()}
            else:
                knowledge_map = {}

            # 合并主问题和变体结果
            combined_results = []

            # 主问题结果
            for row in main_results:
                # 余弦距离转为相似度分数（1 - distance）
                score = 1.0 - float(row.distance)
                combined_results.append({
                    "knowledge_id": row.id,
                    "question": row.question,
                    "answer": row.answer,
                    "categories": row.categories or [],
                    "match_score": score,
                    "match_method": "vector",
                    "matched_via": "main_question",
                    "variant_id": None,
                })

            # 变体结果
            for row in variant_results:
                knowledge = knowledge_map.get(row.knowledge_id)
                if knowledge:
                    score = 1.0 - float(row.distance)
                    combined_results.append({
                        "knowledge_id": row.knowledge_id,
                        "question": knowledge.question,
                        "answer": knowledge.answer,
                        "categories": knowledge.categories or [],
                        "match_score": score,
                        "match_method": "vector",
                        "matched_via": "variant",
                        "variant_id": row.variant_id,
                    })

            # 按分数排序并去重
            combined_results.sort(key=lambda x: x["match_score"], reverse=True)
            seen = set()
            unique_results = []
            for result in combined_results:
                if result["knowledge_id"] not in seen:
                    seen.add(result["knowledge_id"])
                    unique_results.append(result)
                if len(unique_results) >= top_k:
                    break

            logger.info("vector_search_completed", results_count=len(unique_results))
            return unique_results

        except Exception as e:
            logger.error("vector_search_failed", error=str(e))
            raise

    async def _bm25_search(
        self,
        query: str,
        scope_type: str,
        scope_id: UUID,
        tenant_id: UUID,
        include_company: bool,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        BM25全文检索

        Args:
            query: 查询文本
            scope_type: 作用域类型
            scope_id: 作用域ID
            tenant_id: 租户ID
            include_company: 是否包含公司级知识
            top_k: 返回Top K结果

        Returns:
            检索结果列表
        """
        try:
            # 构建scope条件
            scope_conditions = []
            if scope_type == "job":
                scope_conditions.append(
                    and_(
                        JobKnowledgeBase.scope_type == "job",
                        JobKnowledgeBase.scope_id == scope_id
                    )
                )
                if include_company:
                    scope_conditions.append(
                        and_(
                            JobKnowledgeBase.scope_type == "company",
                            JobKnowledgeBase.scope_id == tenant_id
                        )
                    )
            else:
                scope_conditions.append(
                    and_(
                        JobKnowledgeBase.scope_type == scope_type,
                        JobKnowledgeBase.scope_id == scope_id
                    )
                )

            # PostgreSQL全文检索
            # 使用 ts_rank_cd 进行BM25近似排序
            bm25_query = (
                select(
                    JobKnowledgeBase.id,
                    JobKnowledgeBase.question,
                    JobKnowledgeBase.answer,
                    JobKnowledgeBase.categories,
                    func.ts_rank_cd(
                        func.to_tsvector("simple", JobKnowledgeBase.question + " " + func.coalesce(JobKnowledgeBase.keywords, "")),
                        func.plainto_tsquery("simple", query)
                    ).label("rank")
                )
                .where(
                    and_(
                        JobKnowledgeBase.tenant_id == tenant_id,
                        or_(*scope_conditions),
                        JobKnowledgeBase.status == "active",
                        func.to_tsvector("simple", JobKnowledgeBase.question + " " + func.coalesce(JobKnowledgeBase.keywords, "")).op("@@")(
                            func.plainto_tsquery("simple", query)
                        )
                    )
                )
                .order_by(text("rank DESC"))
                .limit(top_k)
            )

            result = await self.db.execute(bm25_query)
            rows = result.fetchall()

            results = []
            for row in rows:
                results.append({
                    "knowledge_id": row.id,
                    "question": row.question,
                    "answer": row.answer,
                    "categories": row.categories or [],
                    "match_score": float(row.rank),
                    "match_method": "bm25",
                    "matched_via": "main_question",
                    "variant_id": None,
                })

            logger.info("bm25_search_completed", results_count=len(results))
            return results

        except Exception as e:
            logger.error("bm25_search_failed", error=str(e))
            raise

    async def _hybrid_search(
        self,
        query: str,
        scope_type: str,
        scope_id: UUID,
        tenant_id: UUID,
        include_company: bool,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        混合检索（RRF融合）

        Args:
            query: 查询文本
            scope_type: 作用域类型
            scope_id: 作用域ID
            tenant_id: 租户ID
            include_company: 是否包含公司级知识
            top_k: 返回Top K结果

        Returns:
            检索结果列表
        """
        try:
            # 向量检索
            vector_results = await self._vector_search(
                query, scope_type, scope_id, tenant_id, include_company, top_k * 2
            )

            # BM25检索
            bm25_results = await self._bm25_search(
                query, scope_type, scope_id, tenant_id, include_company, top_k * 2
            )

            # RRF融合
            merged_results = self._rrf_merge(vector_results, bm25_results, k=60)

            # 返回Top K
            final_results = merged_results[:top_k]

            logger.info("hybrid_search_completed",
                       vector_count=len(vector_results),
                       bm25_count=len(bm25_results),
                       final_count=len(final_results))

            return final_results

        except Exception as e:
            logger.error("hybrid_search_failed", error=str(e))
            raise

    def _rrf_merge(
        self,
        vector_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        RRF (Reciprocal Rank Fusion) 融合排序

        Args:
            vector_results: 向量检索结果
            bm25_results: BM25检索结果
            k: RRF常数（默认60）

        Returns:
            融合后的结果列表
        """
        scores = defaultdict(float)
        items = {}

        # 向量检索贡献
        for rank, item in enumerate(vector_results, start=1):
            kid = str(item["knowledge_id"])
            scores[kid] += 1.0 / (k + rank)
            items[kid] = item

        # BM25检索贡献
        for rank, item in enumerate(bm25_results, start=1):
            kid = str(item["knowledge_id"])
            scores[kid] += 1.0 / (k + rank)
            if kid not in items:
                items[kid] = item

        # 排序并合并
        sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        result = []
        for kid, score in sorted_ids:
            item = items[kid].copy()
            item["match_score"] = score
            item["match_method"] = "hybrid"
            result.append(item)

        return result

    async def _simple_filter(
        self,
        scope_type: str,
        scope_id: UUID,
        tenant_id: UUID,
        include_company: bool,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        简单过滤（不打分，按创建时间）

        Args:
            scope_type: 作用域类型
            scope_id: 作用域ID
            tenant_id: 租户ID
            include_company: 是否包含公司级知识
            top_k: 返回Top K结果

        Returns:
            检索结果列表
        """
        try:
            # 构建scope条件
            scope_conditions = []
            if scope_type == "job":
                scope_conditions.append(
                    and_(
                        JobKnowledgeBase.scope_type == "job",
                        JobKnowledgeBase.scope_id == scope_id
                    )
                )
                if include_company:
                    scope_conditions.append(
                        and_(
                            JobKnowledgeBase.scope_type == "company",
                            JobKnowledgeBase.scope_id == tenant_id
                        )
                    )
            else:
                scope_conditions.append(
                    and_(
                        JobKnowledgeBase.scope_type == scope_type,
                        JobKnowledgeBase.scope_id == scope_id
                    )
                )

            # 简单查询
            simple_query = (
                select(
                    JobKnowledgeBase.id,
                    JobKnowledgeBase.question,
                    JobKnowledgeBase.answer,
                    JobKnowledgeBase.categories,
                )
                .where(
                    and_(
                        JobKnowledgeBase.tenant_id == tenant_id,
                        or_(*scope_conditions),
                        JobKnowledgeBase.status == "active"
                    )
                )
                .order_by(JobKnowledgeBase.created_at.desc())
                .limit(top_k)
            )

            async with get_db_context() as db:
                result = await db.execute(simple_query)
                rows = result.fetchall()
                results = []
                for row in rows:
                    results.append({
                        "knowledge_id": row.id,
                        "question": row.question,
                        "answer": row.answer,
                        "categories": row.categories or [],
                        "match_score": 1.0,  # 无打分
                        "match_method": "simple",
                        "matched_via": "main_question",
                        "variant_id": None,
                    })

            logger.info("simple_filter_completed", results_count=len(results))
            return results

        except Exception as e:
            logger.error("simple_filter_failed", error=str(e))
            raise
