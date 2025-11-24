"""
Education History model
"""
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class EducationHistory(Base):
    """教育经历模型"""
    
    __tablename__ = "education_histories"
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
    resume_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="简历ID")
    school = Column(String(200), nullable=False, comment="学校名称")
    degree = Column(String(50), comment="学位，如：本科、硕士、博士")
    major = Column(String(200), comment="专业")
    start_date = Column(String(20), comment="开始日期")
    end_date = Column(String(20), comment="结束日期")
    # 新增字段
    description = Column(Text, comment="教育经历描述")
    sort_order = Column(Integer, default=0, comment="显示排序（越小越靠前）")
    
    
    def __repr__(self) -> str:
        return f"<EducationHistory(id={self.id}, school={self.school}, degree={self.degree})>"

