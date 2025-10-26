"""
Education History model
"""
from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class EducationHistory(Base):
    """教育经历模型"""
    
    __tablename__ = "education_histories"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False, index=True)
    school = Column(String(200), nullable=False, comment="学校名称")
    degree = Column(String(50), comment="学位，如：本科、硕士、博士")
    major = Column(String(200), comment="专业")
    start_date = Column(String(20), comment="开始日期")
    end_date = Column(String(20), comment="结束日期")
    sort_order = Column(Integer, default=0, comment="显示排序（越小越靠前）")
    
    # 关系
    resume = relationship("Resume", back_populates="education_histories")
    
    def __repr__(self) -> str:
        return f"<EducationHistory(id={self.id}, school={self.school}, degree={self.degree})>"

