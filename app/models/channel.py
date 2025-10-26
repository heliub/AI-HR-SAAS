"""
Channel model
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Channel(Base):
    """招聘渠道模型"""
    
    __tablename__ = "channels"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, comment="渠道名称")
    type = Column(String(20), nullable=False, index=True, 
                 comment="渠道类型: job-board-招聘网站, social-media-社交媒体, referral-内推, agency-猎头, website-官网")
    status = Column(String(20), nullable=False, default="active", index=True, 
                   comment="渠道状态: active-激活, inactive-停用")
    applicants_count = Column(Integer, default=0, comment="该渠道总申请人数（冗余字段）")
    annual_cost = Column(Numeric(10, 2), comment="年度成本")
    cost_currency = Column(String(10), default='CNY', comment="货币单位")
    api_key = Column(Text, comment="API密钥（用于对接第三方平台）")
    contact_person = Column(String(100), comment="渠道联系人")
    contact_email = Column(String(255), comment="渠道联系邮箱")
    description = Column(Text, comment="渠道描述")
    last_sync_at = Column(DateTime(timezone=True), comment="最后同步时间")
    
    # 关系
    job_channels = relationship("JobChannel", back_populates="channel", lazy="dynamic")
    resumes = relationship("Resume", back_populates="source_channel", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<Channel(id={self.id}, name={self.name}, type={self.type})>"

