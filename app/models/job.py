"""
Job model
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Job(Base):
    """职位模型"""
    
    __tablename__ = "jobs"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False, comment="职位标题")
    department = Column(String(100), nullable=False, comment="所属部门")
    location = Column(String(100), nullable=False, comment="工作地点")
    type = Column(String(20), nullable=False, comment="职位类型: full-time-全职, part-time-兼职, contract-合同, intern-实习")
    status = Column(String(20), nullable=False, default="draft", index=True, comment="职位状态: open-开放, closed-关闭, draft-草稿")
    min_salary = Column(Integer, comment="最低薪资（单位：元/月）")
    max_salary = Column(Integer, comment="最高薪资（单位：元/月）")
    description = Column(Text, comment="职位描述")
    requirements = Column(ARRAY(Text), comment="职位要求列表（TEXT数组）")
    preferred_schools = Column(ARRAY(Text), comment="偏好学校列表（TEXT数组）")
    recruitment_invitation = Column(Text, comment="招聘邀请语")
    min_age = Column(Integer, comment="最低年龄要求")
    max_age = Column(Integer, comment="最高年龄要求")
    gender = Column(String(20), comment="性别要求: male-男, female-女, unlimited-不限")
    education = Column(String(100), comment="学历要求")
    job_level = Column(String(50), comment="职级要求，如：P6-P7")
    applicants_count = Column(Integer, default=0, comment="申请人数（冗余字段）")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, comment="创建人用户ID")
    published_at = Column(DateTime(timezone=True), comment="发布时间")
    closed_at = Column(DateTime(timezone=True), comment="关闭时间")
    
    # 关系
    tenant = relationship("Tenant", back_populates="jobs")
    created_by_user = relationship("User", back_populates="jobs")
    resumes = relationship("Resume", back_populates="job", lazy="dynamic")
    ai_match_results = relationship("AIMatchResult", back_populates="job", lazy="dynamic")
    job_channels = relationship("JobChannel", back_populates="job", lazy="dynamic")
    recruitment_tasks = relationship("RecruitmentTask", back_populates="job", lazy="dynamic")
    
    @property
    def salary(self) -> Optional[str]:
        """将 min_salary 和 max_salary 组合成字符串格式"""
        if self.min_salary and self.max_salary:
            # 转换为 K 格式
            min_k = self.min_salary // 1000
            max_k = self.max_salary // 1000
            return f"{min_k}K-{max_k}K"
        elif self.min_salary:
            min_k = self.min_salary // 1000
            return f"{min_k}K+"
        elif self.max_salary:
            max_k = self.max_salary // 1000
            return f"{max_k}K以下"
        return None
    
    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title={self.title}, status={self.status})>"

