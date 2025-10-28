"""
Project Experience model
"""
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class ProjectExperience(Base):
    """项目经历模型"""
    
    __tablename__ = "project_experiences"
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
    resume_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="简历ID")
    project_name = Column(String(200), nullable=False, comment="项目名称")
    role = Column(String(100), comment="在项目中的角色")
    start_date = Column(String(20), comment="开始日期")
    end_date = Column(String(20), comment="结束日期")
    description = Column(Text, comment="项目描述")
    technologies = Column(Text, comment="技术栈列表（多个技术用分隔符分开，如逗号）")
    sort_order = Column(Integer, default=0, comment="显示排序（越小越靠前）")
    
    
    def __repr__(self) -> str:
        return f"<ProjectExperience(id={self.id}, project_name={self.project_name})>"

