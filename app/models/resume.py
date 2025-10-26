"""
Resume model
"""
from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Resume(Base):
    """简历模型"""
    
    __tablename__ = "resumes"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    candidate_name = Column(String(100), nullable=False, comment="候选人姓名")
    email = Column(String(255), index=True, comment="候选人邮箱")
    phone = Column(String(50), comment="候选人电话")
    position = Column(String(200), nullable=False, comment="应聘职位")
    status = Column(String(20), nullable=False, default="pending", index=True, 
                   comment="简历状态: pending-待处理, reviewing-审核中, interview-面试中, offered-已发offer, rejected-已拒绝")
    source = Column(String(100), comment="简历来源渠道名称")
    source_channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, comment="来源渠道ID")
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True, index=True, comment="应聘职位ID")
    experience_years = Column(String(20), comment="工作年限，如：5年")
    education_level = Column(String(50), comment="学历水平，如：本科、硕士")
    age = Column(Integer, comment="年龄")
    gender = Column(String(20), comment="性别: male-男, female-女")
    location = Column(String(100), comment="所在城市")
    school = Column(String(200), comment="毕业院校")
    major = Column(String(200), comment="专业")
    skills = Column(ARRAY(Text), comment="技能列表（TEXT数组）")
    resume_url = Column(Text, comment="简历文件URL")
    conversation_summary = Column(Text, comment="AI对话总结")
    submitted_at = Column(DateTime(timezone=True), comment="简历投递时间")
    
    # 关系
    job = relationship("Job", back_populates="resumes")
    source_channel = relationship("Channel", back_populates="resumes")
    work_experiences = relationship("WorkExperience", back_populates="resume", lazy="dynamic")
    project_experiences = relationship("ProjectExperience", back_populates="resume", lazy="dynamic")
    education_histories = relationship("EducationHistory", back_populates="resume", lazy="dynamic")
    job_preferences = relationship("JobPreference", back_populates="resume", uselist=False, lazy="selectin")
    ai_match_results = relationship("AIMatchResult", back_populates="resume", lazy="dynamic")
    candidate_chat_history = relationship("CandidateChatHistory", back_populates="resume", lazy="dynamic")
    interviews = relationship("Interview", back_populates="candidate", lazy="dynamic")
    email_logs = relationship("EmailLog", back_populates="resume", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, candidate_name={self.candidate_name}, status={self.status})>"

