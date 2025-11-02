"""
Job Knowledge Base model
"""
from typing import Optional

from sqlalchemy import Column, String, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector

from app.models.base import Base


class JobKnowledgeBase(Base):
    """岗位/公司知识库主表模型"""

    __tablename__ = "job_knowledge_base"

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
    user_id = Column(UUID(as_uuid=True), comment="创建者HR用户ID")

    # 作用域
    scope_type = Column(String(20), nullable=False, index=True, comment="作用域类型: company-公司级, job-岗位级")
    scope_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="作用域ID")

    # 分类（支持多标签）
    categories = Column(String(2000), comment="分类标签，逗号分隔的字符串，如：salary,benefits,culture")

    # 问答内容
    question = Column(Text, nullable=False, comment="标准问题")
    answer = Column(Text, nullable=False, comment="标准答案")

    # 检索字段
    keywords = Column(Text, comment="BM25关键词（逗号分隔）")
    question_embedding = Column(Vector(2048), comment="问题向量（2048维）")

    # 扩展字段
    meta_data = Column(JSONB, comment="扩展元数据")

    # 状态
    status = Column(String(20), nullable=False, default="active", index=True, comment="状态: active-启用, archived-归档, deleted-已删除")

    # 审计字段
    created_by = Column(UUID(as_uuid=True), comment="创建人用户ID")
    updated_by = Column(UUID(as_uuid=True), comment="最后更新人用户ID")

    def __repr__(self) -> str:
        return f"<JobKnowledgeBase(id={self.id}, scope_type={self.scope_type}, question={self.question[:30]}...)>"
