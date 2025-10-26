"""
Job Preference model
"""
from sqlalchemy import Column, String, ForeignKey, Date, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class JobPreference(Base):
    """求职意向模型"""
    
    __tablename__ = "job_preferences"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False, index=True)
    expected_salary = Column(String(50), comment="期望薪资")
    preferred_locations = Column(ARRAY(Text), comment="期望工作地点列表（TEXT数组）")
    job_type = Column(String(50), comment="期望工作类型，如：全职、兼职")
    available_date = Column(Date, comment="最早到岗日期")
    
    # 关系
    resume = relationship("Resume", back_populates="job_preferences")
    
    def __repr__(self) -> str:
        return f"<JobPreference(id={self.id}, resume_id={self.resume_id})>"

