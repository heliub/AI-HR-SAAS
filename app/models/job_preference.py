"""
Job Preference model
"""
from sqlalchemy import Column, String, Date, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class JobPreference(Base):
    """求职意向模型"""
    
    __tablename__ = "job_preferences"
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
    resume_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="简历ID")
    expected_salary = Column(String(50), comment="期望薪资")
    preferred_locations = Column(ARRAY(Text), comment="期望工作地点列表（TEXT数组）")
    job_type = Column(String(50), comment="期望工作类型，如：全职、兼职")
    available_date = Column(Date, comment="最早到岗日期")
    
    
    def __repr__(self) -> str:
        return f"<JobPreference(id={self.id}, resume_id={self.resume_id})>"

