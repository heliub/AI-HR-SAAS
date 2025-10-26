"""
Activity Log model
"""
from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship

from app.models.base import Base


class ActivityLog(Base):
    """操作日志模型"""
    
    __tablename__ = "activity_logs"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, comment="租户ID（可为空，系统级操作）")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, comment="操作用户ID")
    action = Column(String(100), nullable=False, comment="操作类型，如：create_job, update_resume")
    entity_type = Column(String(50), index=True, comment="实体类型，如：job, resume, interview")
    entity_id = Column(UUID(as_uuid=True), index=True, comment="实体ID")
    details = Column(JSONB, comment="详细信息（JSON格式）")
    ip_address = Column(INET, comment="操作IP地址")
    user_agent = Column(Text, comment="浏览器User-Agent")
    
    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id}, action={self.action}, entity_type={self.entity_type})>"

