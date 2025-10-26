"""
Job Channel model
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class JobChannel(Base):
    """职位发布渠道关联模型"""
    
    __tablename__ = "job_channels"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id"), nullable=False, index=True)
    published_at = Column(DateTime(timezone=True), comment="发布时间")
    external_id = Column(String(100), comment="外部平台的职位ID")
    external_url = Column(Text, comment="外部平台的职位URL")
    views_count = Column(Integer, default=0, comment="浏览次数")
    clicks_count = Column(Integer, default=0, comment="点击次数")
    
    # 关系
    job = relationship("Job", back_populates="job_channels")
    channel = relationship("Channel", back_populates="job_channels")
    
    def __repr__(self) -> str:
        return f"<JobChannel(id={self.id}, job_id={self.job_id}, channel_id={self.channel_id})>"

