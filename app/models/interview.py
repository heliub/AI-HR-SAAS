"""
Interview model
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, Date, Time
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from app.models.base import Base


class Interview(Base):
    """面试模型"""
    
    __tablename__ = "interviews"
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True, comment="创建该面试的HR用户ID")
    candidate_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="候选人简历ID")
    candidate_name = Column(String(100), nullable=False, comment="候选人姓名（冗余字段）")
    position = Column(String(200), nullable=False, comment="应聘职位（冗余字段）")
    interview_date = Column(Date, nullable=False, comment="面试日期")
    interview_time = Column(Time, nullable=False, comment="面试时间")
    interviewer = Column(String(100), nullable=False, comment="面试官姓名")
    interviewer_title = Column(String(100), comment="面试官职位")
    type = Column(String(20), nullable=False, comment="面试类型: phone-电话面试, video-视频面试, onsite-现场面试")
    status = Column(String(20), nullable=False, default="scheduled", index=True,
                   comment="面试状态: scheduled-已安排, completed-已完成, cancelled-已取消, rescheduled-已改期")
    location = Column(String(200), comment="面试地点（现场面试）")
    meeting_link = Column(Text, comment="会议链接（视频面试）")
    notes = Column(Text, comment="面试备注")
    feedback = Column(Text, comment="面试反馈")
    rating = Column(Integer, comment="面试评分（1-5分）")
    created_at = Column(DateTime(timezone=True), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), comment="更新时间")
    cancelled_at = Column(DateTime(timezone=True), comment="取消时间")
    cancellation_reason = Column(Text, comment="取消原因")


    def __repr__(self) -> str:
        return f"<Interview(id={self.id}, candidate_name={self.candidate_name}, status={self.status})>"

