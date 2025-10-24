"""
Email Account model
"""
from datetime import datetime

from sqlalchemy import Column, BigInteger, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base


class EmailAccount(Base):
    """邮箱账号模型"""
    
    __tablename__ = "email_accounts"
    
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True, comment="邮箱地址")
    protocol = Column(
        String(20), 
        nullable=False,
        comment="协议: exchange, imap, pop3"
    )
    credentials = Column(JSONB, nullable=False, comment="加密存储的凭证")
    settings = Column(JSONB, comment="邮箱配置")
    status = Column(
        String(20), 
        default="active",
        index=True,
        comment="状态: active, invalid, suspended"
    )
    last_synced_at = Column(DateTime, nullable=True, comment="最后同步时间")
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('tenant_id', 'user_id', 'email', name='uq_email_account'),
    )
    
    def __repr__(self) -> str:
        return f"<EmailAccount(id={self.id}, email={self.email}, protocol={self.protocol})>"

