"""
Job Channel model
"""
from sqlalchemy import Column, String, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class JobChannel(Base):
    """职位发布渠道关联模型"""
    
    __tablename__ = "job_channels"
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
    job_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="职位ID")
    channel_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="渠道ID")
    published_at = Column(DateTime(timezone=True), comment="发布时间")
    external_id = Column(String(100), comment="外部平台的职位ID")
    external_url = Column(Text, comment="外部平台的职位URL")
    views_count = Column(Integer, default=0, comment="浏览次数")
    clicks_count = Column(Integer, default=0, comment="点击次数")
    
    
    def __repr__(self) -> str:
        return f"<JobChannel(id={self.id}, job_id={self.job_id}, channel_id={self.channel_id})>"

