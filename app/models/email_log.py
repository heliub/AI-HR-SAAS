"""
Email Log model
"""
from sqlalchemy import Column, String, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class EmailLog(Base):
    """邮件发送记录模型"""
    
    __tablename__ = "email_logs"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    recipient_email = Column(String(255), nullable=False, index=True, comment="收件人邮箱")
    subject = Column(String(500), nullable=False, comment="邮件主题")
    content = Column(Text, comment="邮件内容")
    template_name = Column(String(100), comment="使用的邮件模板名称")
    status = Column(String(20), index=True, comment="发送状态: pending-待发送, sent-已发送, failed-发送失败")
    error_message = Column(Text, comment="错误信息（发送失败时）")
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), index=True, comment="关联简历ID")
    sent_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), comment="发送人用户ID")
    sent_at = Column(DateTime(timezone=True), comment="实际发送时间")
    
    # 关系
    resume = relationship("Resume", back_populates="email_logs")
    
    def __repr__(self) -> str:
        return f"<EmailLog(id={self.id}, recipient_email={self.recipient_email}, status={self.status})>"

