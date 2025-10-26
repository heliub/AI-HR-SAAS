"""
Work Experience model
"""
from sqlalchemy import Column, String, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class WorkExperience(Base):
    """工作经历模型"""
    
    __tablename__ = "work_experiences"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False, index=True)
    company = Column(String(200), nullable=False, comment="公司名称")
    position = Column(String(200), nullable=False, comment="职位")
    start_date = Column(String(20), comment="开始日期，如：2021-03")
    end_date = Column(String(20), comment="结束日期，如：至今、2024-12")
    description = Column(Text, comment="工作描述")
    sort_order = Column(Integer, default=0, comment="显示排序（越小越靠前）")
    
    # 关系
    resume = relationship("Resume", back_populates="work_experiences")
    
    def __repr__(self) -> str:
        return f"<WorkExperience(id={self.id}, company={self.company}, position={self.position})>"

