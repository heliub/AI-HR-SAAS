"""
Knowledge Embedding Service

负责知识库的embedding生成
"""
import asyncio
import os
from typing import List, Optional
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.ai.llm.providers.volcengine_embedding import VolcengineEmbeddingClient
from app.models.job_knowledge_base import JobKnowledgeBase
from app.models.knowledge_question_variant import KnowledgeQuestionVariant
import structlog
from app.ai.llm.factory import get_embedding

logger = structlog.get_logger(__name__)


class KnowledgeEmbeddingService:
    """知识库Embedding生成服务"""

    # 火山引擎embedding模型
    EMBEDDING_MODEL = "doubao-embedding-text-240715"
    EMBEDDING_DIMENSION = 2048

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        # 线程池（用于批量异步生成）
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

        # 初始化embedding client

        self.embedding_client = get_embedding(provider="volcengine")

    async def generate_for_text(self, text: str) -> List[float]:
        """
        为单个文本生成embedding（同步）

        Args:
            text: 输入文本

        Returns:
            Embedding向量

        Raises:
            LLMError: 生成失败
        """
        try:
            logger.info("generating_embedding_for_text", text_length=len(text))
            embedding = await self.embedding_client.embed_text(
                text=text,
                model=self.EMBEDDING_MODEL,
            )
            logger.info("embedding_generated_successfully", dimension=len(embedding))
            return embedding
        except Exception as e:
            logger.error("failed_to_generate_embedding", error=str(e), text_length=len(text))
            raise

    async def generate_for_knowledge(
        self,
        knowledge_id: UUID,
        tenant_id: UUID
    ) -> bool:
        """
        为知识库条目生成embedding（同步）

        Args:
            knowledge_id: 知识库ID
            tenant_id: 租户ID

        Returns:
            是否成功

        Raises:
            Exception: 生成失败
        """
        try:
            # 获取知识库
            query = select(JobKnowledgeBase).where(
                JobKnowledgeBase.id == knowledge_id,
                JobKnowledgeBase.tenant_id == tenant_id
            )
            result = await self.db.execute(query)
            knowledge = result.scalar()

            if not knowledge:
                logger.warning("knowledge_not_found", knowledge_id=knowledge_id)
                return False

            # 生成embedding
            embedding = await self.generate_for_text(knowledge.question)

            # 更新数据库
            stmt = (
                update(JobKnowledgeBase)
                .where(JobKnowledgeBase.id == knowledge_id)
                .values(question_embedding=embedding)
            )
            await self.db.execute(stmt)
            await self.db.commit()

            logger.info("knowledge_embedding_updated", knowledge_id=knowledge_id)
            return True

        except Exception as e:
            logger.error("failed_to_generate_knowledge_embedding",
                        knowledge_id=knowledge_id, error=str(e))
            await self.db.rollback()
            raise

    async def generate_for_variant(
        self,
        variant_id: UUID,
        tenant_id: UUID
    ) -> bool:
        """
        为问题变体生成embedding（同步）

        Args:
            variant_id: 变体ID
            tenant_id: 租户ID

        Returns:
            是否成功

        Raises:
            Exception: 生成失败
        """
        try:
            # 获取变体
            query = select(KnowledgeQuestionVariant).where(
                KnowledgeQuestionVariant.id == variant_id,
                KnowledgeQuestionVariant.tenant_id == tenant_id
            )
            result = await self.db.execute(query)
            variant = result.scalar()

            if not variant:
                logger.warning("variant_not_found", variant_id=variant_id)
                return False

            # 生成embedding
            embedding = await self.generate_for_text(variant.variant_question)

            # 更新数据库
            stmt = (
                update(KnowledgeQuestionVariant)
                .where(KnowledgeQuestionVariant.id == variant_id)
                .values(variant_embedding=embedding)
            )
            await self.db.execute(stmt)
            await self.db.commit()

            logger.info("variant_embedding_updated", variant_id=variant_id)
            return True

        except Exception as e:
            logger.error("failed_to_generate_variant_embedding",
                        variant_id=variant_id, error=str(e))
            await self.db.rollback()
            raise

    async def generate_batch_async(
        self,
        knowledge_ids: List[UUID],
        tenant_id: UUID
    ) -> None:
        """
        批量异步生成embedding（后台线程）

        Args:
            knowledge_ids: 知识库ID列表
            tenant_id: 租户ID

        Note:
            此方法会立即返回，实际生成在后台线程中进行
        """
        def _batch_task():
            """后台任务：批量生成embedding"""
            # 创建新的event loop（在线程中）
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    self._process_batch(knowledge_ids, tenant_id)
                )
            finally:
                loop.close()

        # 提交到线程池，立即返回
        self.thread_pool.submit(_batch_task)
        logger.info("batch_embedding_task_submitted", count=len(knowledge_ids))

    async def _process_batch(
        self,
        knowledge_ids: List[UUID],
        tenant_id: UUID
    ) -> None:
        """
        实际的批量处理逻辑（内部方法）

        Args:
            knowledge_ids: 知识库ID列表
            tenant_id: 租户ID
        """
        logger.info("starting_batch_embedding_processing", count=len(knowledge_ids))

        success_count = 0
        failed_count = 0

        # 在独立线程中创建新的数据库会话
        from app.infrastructure.database.session import async_session_maker
        
        async with async_session_maker() as new_session:
            for kid in knowledge_ids:
                try:
                    # 使用新的会话创建 embedding 服务实例
                    new_embedding_service = KnowledgeEmbeddingService(new_session)
                    await new_embedding_service.generate_for_knowledge(kid, tenant_id)
                    success_count += 1
                except Exception as e:
                    logger.error("batch_embedding_failed_for_item",
                               knowledge_id=kid, error=str(e))
                    failed_count += 1

        logger.info("batch_embedding_completed",
                   total=len(knowledge_ids),
                   success=success_count,
                   failed=failed_count)

    async def generate_batch_variants_async(
        self,
        variant_ids: List[UUID],
        tenant_id: UUID
    ) -> None:
        """
        批量异步生成变体embedding（后台线程）

        Args:
            variant_ids: 变体ID列表
            tenant_id: 租户ID
        """
        def _batch_task():
            """后台任务：批量生成变体embedding"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    self._process_batch_variants(variant_ids, tenant_id)
                )
            finally:
                loop.close()

        self.thread_pool.submit(_batch_task)
        logger.info("batch_variant_embedding_task_submitted", count=len(variant_ids))

    async def _process_batch_variants(
        self,
        variant_ids: List[UUID],
        tenant_id: UUID
    ) -> None:
        """
        实际的批量变体处理逻辑（内部方法）

        Args:
            variant_ids: 变体ID列表
            tenant_id: 租户ID
        """
        logger.info("starting_batch_variant_embedding_processing", count=len(variant_ids))

        success_count = 0
        failed_count = 0

        # 在独立线程中创建新的数据库会话
        from app.infrastructure.database.session import async_session_maker
        
        async with async_session_maker() as new_session:
            for vid in variant_ids:
                try:
                    # 使用新的会话创建 embedding 服务实例
                    new_embedding_service = KnowledgeEmbeddingService(new_session)
                    await new_embedding_service.generate_for_variant(vid, tenant_id)
                    success_count += 1
                except Exception as e:
                    logger.error("batch_variant_embedding_failed_for_item",
                               variant_id=vid, error=str(e))
                    failed_count += 1

        logger.info("batch_variant_embedding_completed",
                   total=len(variant_ids),
                   success=success_count,
                   failed=failed_count)
