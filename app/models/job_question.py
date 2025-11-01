"""
Job Question model
"""
from typing import Optional

from sqlalchemy import Column, String, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class JobQuestion(Base):
    """职位问题预设模型"""
    
    __tablename__ = "job_questions"
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="创建问题的HR用户ID")
    job_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="关联职位ID")
    question = Column(Text, nullable=False, comment="问题内容")
    question_type = Column(String(20), nullable=False, comment="问题类型: information-信息采集, assessment-考察评估")
    is_required = Column(Boolean, nullable=False, default=False, comment="是否必须满足该要求")
    evaluation_criteria = Column(Text, comment="判断标准（考察类问题使用）")
    sort_order = Column(Integer, default=0, comment="显示排序（越小越靠前）")
    status = Column(String(20), nullable=False, default="active", index=True, comment="状态: active-启用, deleted-已删除")
    
    def __repr__(self) -> str:
        return f"<JobQuestion(id={self.id}, job_id={self.job_id}, question_type={self.question_type})>"
