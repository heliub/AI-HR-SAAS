"""
Auth Token model
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class AuthToken(Base):
    """认证Token模型"""
    
    __tablename__ = "auth_tokens"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(500), nullable=False, index=True, comment="JWT Token字符串")
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True, comment="Token过期时间")
    is_revoked = Column(Boolean, default=False, comment="是否已撤销")
    
    def __repr__(self) -> str:
        return f"<AuthToken(id={self.id}, user_id={self.user_id})>"

