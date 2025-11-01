"""
Knowledge Question Variant model
"""
from typing import Optional

from sqlalchemy import Column, String, Text, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from app.models.base import Base


class KnowledgeQuestionVariant(Base):
    """知识库问题变体模型"""

    __tablename__ = "knowledge_question_variants"

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
    knowledge_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="关联的知识库条目ID")

    # 冗余scope字段（查询性能优化）
    scope_type = Column(String(20), nullable=False, index=True, comment="作用域类型")
    scope_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="作用域ID")

    # 变体内容
    variant_question = Column(Text, nullable=False, comment="变体问题")
    variant_embedding = Column(Vector(2048), comment="变体问题向量（2048维）")

    # 来源标记
    source = Column(String(20), nullable=False, default="manual", comment="来源: manual-手动, ai_generated-AI生成, user_feedback-候选人反馈")
    confidence_score = Column(DECIMAL(3, 2), comment="AI生成时的置信度（0.00-1.00）")

    # 状态
    status = Column(String(20), nullable=False, default="active", index=True, comment="状态: active-启用, deleted-已删除")

    def __repr__(self) -> str:
        return f"<KnowledgeQuestionVariant(id={self.id}, knowledge_id={self.knowledge_id}, variant={self.variant_question[:30]}...)>"
