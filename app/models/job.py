"""
Job model
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Job(Base):
    """职位模型"""
    
    __tablename__ = "jobs"
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="租户ID")
    user_id = Column(UUID(as_uuid=True),  index=True, comment="创建该职位的HR用户ID")
    title = Column(String(200), nullable=False, comment="职位标题")
    department = Column(String(100),  comment="所属部门")
    location = Column(String(100),  comment="工作地点")
    type = Column(String(20),  comment="职位类型: full-time-全职, part-time-兼职, contract-合同, intern-实习")
    status = Column(String(20), nullable=False, default="draft", index=True, comment="职位状态: open-开放, closed-关闭, draft-草稿, deleted-已删除")
    min_salary = Column(Integer,  comment="最低薪资（单位：元/月）")
    max_salary = Column(Integer,  comment="最高薪资（单位：元/月）")
    description = Column(Text,  comment="职位描述")
    requirements = Column(Text,  comment="职位要求（多个要求用分隔符分开，如逗号）")
    preferred_schools = Column(Text,  comment="偏好学校（多个学校用分隔符分开，如逗号）")
    recruitment_invitation = Column(Text,  comment="招聘邀请语")
    min_age = Column(Integer,  comment="最低年龄要求")
    max_age = Column(Integer,  comment="最高年龄要求")
    gender = Column(String(20),  comment="性别要求: male-男, female-女, unlimited-不限")
    education = Column(String(100),  comment="学历要求")
    job_level = Column(String(50),  comment="职级要求，如：P6-P7")
    applicants_count = Column(Integer, nullable=False, default=0, comment="申请人数（冗余字段）")
    created_by = Column(UUID(as_uuid=True),  index=True, comment="创建人用户ID")
    published_at = Column(DateTime(timezone=True),  comment="发布时间")
    closed_at = Column(DateTime(timezone=True),  comment="关闭时间")
    # LinkedIn/JobStreet 标准字段
    company = Column(String(200),  comment="公司名称")
    workplace_type = Column(String(20),  comment="工作场所类型: on-site-现场办公, hybrid-混合办公, remote-远程办公")
    pay_type = Column(String(20),  comment="薪资类型: hourly-时薪, monthly-月薪, annual-年薪, annual_plus_commission-年薪加提成")
    pay_currency = Column(String(10), nullable=False, default="CNY", comment="薪资货币")
    pay_shown_on_ad = Column(Boolean, nullable=False, default=False, comment="是否在广告中显示薪资")
    category = Column(String(100),  comment="职位分类")
    
      
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

