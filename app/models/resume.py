"""
Resume model
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Date
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Resume(Base):
    """简历模型"""
    
    __tablename__ = "resumes"
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
    user_id = Column(UUID(as_uuid=True), index=True, comment="处理该简历的HR用户ID")
    candidate_name = Column(String(100), nullable=False, comment="候选人姓名")
    email = Column(String(255), index=True, comment="候选人邮箱")
    phone = Column(String(50), comment="候选人电话")
    position = Column(String(200), comment="应聘职位")
    status = Column(String(20), nullable=False, default="pending", index=True, 
                   comment="简历状态: pending-待处理, reviewing-审核中, interview-面试中, offered-已发offer, rejected-已拒绝")
    source = Column(String(100), comment="简历来源渠道名称")
    source_channel_id = Column(UUID(as_uuid=True), index=True, comment="来源渠道ID")
    job_id = Column(UUID(as_uuid=True), index=True, comment="应聘职位ID")
    experience_years = Column(String(20), comment="工作年限，如：5年")
    education_level = Column(String(50), comment="学历水平，如：本科、硕士")
    age = Column(Integer, comment="年龄")
    gender = Column(String(20), comment="性别: male-男, female-女")
    location = Column(String(100), comment="所在城市")
    school = Column(String(200), comment="毕业院校")
    major = Column(String(200), comment="专业")
    skills = Column(Text, comment="技能列表（多个技能用分隔符分开，如逗号）")
    resume_url = Column(Text, comment="简历文件URL")
    conversation_summary = Column(Text, comment="AI对话总结")
    is_match = Column(Boolean, comment="是否匹配（基于AI分析结果）")
    match_conclusion = Column(Text, comment="匹配结论（基于AI分析结果）")
    submitted_at = Column(DateTime(timezone=True), comment="简历投递时间")
    # 新增字段
    birth_date = Column(Date, comment="出生日期")
    birth_place = Column(String(100), comment="出生地")
    marital_status = Column(String(20), comment="婚姻状况: single-单身, married-已婚, divorced-离异, widowed-丧偶, unknown-未知")
    job_search_status = Column(String(50), comment="求职状态: actively_looking-积极求职, open_to_opportunities-开放机会, not_looking-不求职, unknown-未知")
    self_introduction = Column(Text, comment="自我介绍")
    
        
    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, candidate_name={self.candidate_name}, status={self.status})>"

