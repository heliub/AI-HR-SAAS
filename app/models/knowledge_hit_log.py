"""
Knowledge Hit Log model
"""
from typing import Optional

from sqlalchemy import Column, String, Text, Integer, DECIMAL
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class KnowledgeHitLog(Base):
    """知识库命中日志模型"""

    __tablename__ = "knowledge_hit_logs"

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")

    # 关联信息
    knowledge_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="命中的知识库条目ID")
    variant_id = Column(UUID(as_uuid=True), comment="如果通过变体命中，记录变体ID")
    conversation_id = Column(UUID(as_uuid=True), index=True, comment="关联的会话ID")

    # 检索信息
    user_question = Column(Text, comment="候选人原始问题")

    # 匹配信息
    match_method = Column(String(20), comment="匹配方法: vector-向量, bm25-全文, hybrid-混合")
    match_score = Column(DECIMAL(5, 4), comment="匹配分数（0.0000-1.0000）")
    rank_position = Column(Integer, comment="在检索结果中的排名位置")

    def __repr__(self) -> str:
        return f"<KnowledgeHitLog(id={self.id}, knowledge_id={self.knowledge_id}, match_method={self.match_method})>"
