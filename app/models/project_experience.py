"""
Project Experience model
"""
from sqlalchemy import Column, String, ForeignKey, Integer, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class ProjectExperience(Base):
    """项目经历模型"""
    
    __tablename__ = "project_experiences"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False, index=True)
    project_name = Column(String(200), nullable=False, comment="项目名称")
    role = Column(String(100), comment="在项目中的角色")
    start_date = Column(String(20), comment="开始日期")
    end_date = Column(String(20), comment="结束日期")
    description = Column(Text, comment="项目描述")
    technologies = Column(ARRAY(Text), comment="技术栈列表（TEXT数组）")
    sort_order = Column(Integer, default=0, comment="显示排序（越小越靠前）")
    
    # 关系
    resume = relationship("Resume", back_populates="project_experiences")
    
    def __repr__(self) -> str:
        return f"<ProjectExperience(id={self.id}, project_name={self.project_name})>"

