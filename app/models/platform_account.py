"""
Platform Account model
"""
from datetime import datetime

from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import Base


class PlatformAccount(Base):
    """三方平台账号模型"""
    
    __tablename__ = "platform_accounts"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(
        String(50), 
        nullable=False,
        index=True,
        comment="平台: linkedin, jobstreet"
    )
    account_name = Column(String(255), comment="账号名称")
    credentials = Column(JSONB, nullable=False, comment="加密存储的凭证")
    settings = Column(JSONB, comment="平台特定配置")
    status = Column(
        String(20), 
        default="active",
        index=True,
        comment="状态: active, invalid, suspended"
    )
    last_validated_at = Column(DateTime, comment="最后验证时间")
    
    def __repr__(self) -> str:
        return f"<PlatformAccount(id={self.id}, platform={self.platform}, status={self.status})>"

