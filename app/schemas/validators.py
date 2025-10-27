"""
数据验证层
使用Pydantic进行严格的数据验证
"""
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, Field, validator, EmailStr, HttpUrl, constr
from pydantic_core import ValidationError
import re

from app.auth.permissions import Role


# 基础验证器
class BaseValidator(BaseModel):
    """基础验证器"""

    class Config:
        str_strip_whitespace = True
        validate_assignment = True
        use_enum_values = True


class ContactInfoValidator(BaseValidator):
    """联系信息验证"""
    phone: Optional[constr(regex=r'^\+?1?\d{9,15}$')] = None
    email: EmailStr
    wechat: Optional[constr(min_length=5, max_length=50)] = None
    linkedin: Optional[HttpUrl] = None


class SalaryValidator(BaseValidator):
    """薪资验证"""
    minSalary: Optional[int] = Field(None, alias="min_salary", ge=0, le=1000000)
    maxSalary: Optional[int] = Field(None, alias="max_salary", ge=0, le=1000000)

    @validator('maxSalary')
    def validate_salary_range(cls, v, values):
        if v is not None and 'minSalary' in values and values['minSalary'] is not None:
            if v < values['minSalary']:
                raise ValueError('最高薪资不能低于最低薪资')
        return v


class DateRangeValidator(BaseValidator):
    """日期范围验证"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v is not None and 'start_date' in values and values['start_date'] is not None:
            if v < values['start_date']:
                raise ValueError('结束日期不能早于开始日期')
        return v


# 简历相关验证器
class ResumeCreateValidator(BaseValidator):
    """简历创建验证"""
    candidate_name: constr(min_length=2, max_length=100) = Field(..., description="候选人姓名")
    email: EmailStr = Field(..., description="邮箱地址")
    phone: Optional[constr(regex=r'^\+?1?\d{9,15}$')] = Field(None, description="手机号码")

    # 职位信息
    position: Optional[constr(max_length=100)] = Field(None, description="目标职位")
    current_company: Optional[constr(max_length=100)] = Field(None, description="当前公司")
    current_position: Optional[constr(max_length=100)] = Field(None, description="当前职位")

    # 薪资期望
    min_salary: Optional[int] = Field(None, ge=0, le=1000000, description="最低期望薪资")
    max_salary: Optional[int] = Field(None, ge=0, le=1000000, description="最高期望薪资")

    # 工作经验
    total_experience: Optional[int] = Field(None, ge=0, le=50, description="总工作经验（年）")

    # 教育背景
    education: Optional[constr(max_length=50)] = Field(None, description="最高学历")
    school: Optional[constr(max_length=100)] = Field(None, description="毕业院校")

    # 技能标签
    skills: Optional[List[constr(max_length=50)]] = Field(default=[], description="技能标签")

    # 个人简介
    summary: Optional[constr(max_length=1000)] = Field(None, description="个人简介")

    @validator('max_salary')
    def validate_salary_range(cls, v, values):
        if v is not None and 'min_salary' in values and values['min_salary'] is not None:
            if v < values['min_salary']:
                raise ValueError('最高期望薪资不能低于最低期望薪资')
        return v

    @validator('candidate_name')
    def validate_name(cls, v):
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z\s]+$', v):
            raise ValueError('姓名只能包含中文、英文字母和空格')
        return v

    @validator('email')
    def validate_email_domain(cls, v):
        # 阻止某些常见的临时邮箱域名
        blocked_domains = ['tempmail.com', '10minutemail.com', 'guerrillamail.com']
        domain = v.split('@')[-1].lower()
        if domain in blocked_domains:
            raise ValueError('不支持使用临时邮箱')
        return v


class ResumeUpdateValidator(BaseValidator):
    """简历更新验证"""
    candidate_name: Optional[constr(min_length=2, max_length=100)] = Field(None, description="候选人姓名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    phone: Optional[constr(regex=r'^\+?1?\d{9,15}$')] = Field(None, description="手机号码")
    position: Optional[constr(max_length=100)] = Field(None, description="目标职位")
    status: Optional[constr(regex=r'^(pending|reviewing|interview|offered|rejected|hired)$')] = Field(
        None, description="简历状态"
    )

    # 薪资期望
    min_salary: Optional[int] = Field(None, ge=0, le=1000000, description="最低期望薪资")
    max_salary: Optional[int] = Field(None, ge=0, le=1000000, description="最高期望薪资")

    @validator('max_salary')
    def validate_salary_range(cls, v, values):
        if v is not None and 'min_salary' in values and values['min_salary'] is not None:
            if v < values['min_salary']:
                raise ValueError('最高期望薪资不能低于最低期望薪资')
        return v


# 工作经验验证器
class WorkExperienceValidator(BaseValidator):
    """工作经验验证"""
    company: constr(min_length=2, max_length=100) = Field(..., description="公司名称")
    position: constr(min_length=2, max_length=100) = Field(..., description="职位名称")
    start_date: date = Field(..., description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    is_current_job: bool = Field(False, description="是否为当前工作")
    description: Optional[constr(max_length=2000)] = Field(None, description="工作描述")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v is not None and 'start_date' in values and values['start_date'] is not None:
            if v < values['start_date']:
                raise ValueError('结束日期不能早于开始日期')
        return v

    @validator('is_current_job')
    def validate_current_job(cls, v, values):
        if v and 'end_date' in values and values['end_date'] is not None:
            raise ValueError('当前工作不能有结束日期')
        return v


# 项目经验验证器
class ProjectExperienceValidator(BaseValidator):
    """项目经验验证"""
    name: constr(min_length=2, max_length=200) = Field(..., description="项目名称")
    role: constr(min_length=2, max_length=100) = Field(..., description="担任角色")
    start_date: date = Field(..., description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    description: constr(min_length=10, max_length=2000) = Field(..., description="项目描述")
    technologies: List[constr(max_length=50)] = Field(..., description="使用技术")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v is not None and 'start_date' in values and values['start_date'] is not None:
            if v < values['start_date']:
                raise ValueError('结束日期不能早于开始日期')
        return v


# 教育背景验证器
class EducationValidator(BaseValidator):
    """教育背景验证"""
    school: constr(min_length=2, max_length=100) = Field(..., description="学校名称")
    degree: constr(min_length=2, max_length=100) = Field(..., description="学位")
    major: constr(min_length=2, max_length=100) = Field(..., description="专业")
    start_date: date = Field(..., description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    is_current: bool = Field(False, description="是否为在读")
    gpa: Optional[float] = Field(None, ge=0.0, le=5.0, description="GPA")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v is not None and 'start_date' in values and values['start_date'] is not None:
            if v < values['start_date']:
                raise ValueError('结束日期不能早于开始日期')
        return v

    @validator('gpa')
    def validate_gpa_format(cls, v):
        if v is not None and (v < 0 or v > 5):
            raise ValueError('GPA必须在0-5之间')
        return v


# 职位相关验证器
class JobCreateValidator(BaseValidator):
    """职位创建验证"""
    title: constr(min_length=2, max_length=100) = Field(..., description="职位名称")
    department: constr(min_length=2, max_length=50) = Field(..., description="部门")
    location: constr(min_length=2, max_length=100) = Field(..., description="工作地点")
    type: constr(regex=r'^(fulltime|parttime|contract|intern)$') = Field(..., description="工作类型")

    # 薪资信息
    min_salary: Optional[int] = Field(None, ge=0, le=1000000, description="最低薪资")
    max_salary: Optional[int] = Field(None, ge=0, le=1000000, description="最高薪资")
    salary_currency: Optional[constr(regex=r'^[A-Z]{3}$')] = Field('CNY', description="薪资货币")

    # 职位要求
    requirements: Optional[constr(max_length=2000)] = Field(None, description="职位要求")
    description: Optional[constr(max_length=5000)] = Field(None, description="职位描述")

    # 招聘偏好
    min_experience: Optional[int] = Field(None, ge=0, le=50, description="最低工作经验（年）")
    max_experience: Optional[int] = Field(None, ge=0, le=50, description="最高工作经验（年）")
    education: Optional[constr(max_length=50)] = Field(None, description="学历要求")

    @validator('max_salary')
    def validate_salary_range(cls, v, values):
        if v is not None and 'min_salary' in values and values['min_salary'] is not None:
            if v < values['min_salary']:
                raise ValueError('最高薪资不能低于最低薪资')
        return v

    @validator('max_experience')
    def validate_experience_range(cls, v, values):
        if v is not None and 'min_experience' in values and values['min_experience'] is not None:
            if v < values['min_experience']:
                raise ValueError('最高经验不能低于最低经验')
        return v


# 用户相关验证器
class UserCreateValidator(BaseValidator):
    """用户创建验证"""
    email: EmailStr = Field(..., description="邮箱地址")
    username: constr(min_length=3, max_length=50, regex=r'^[a-zA-Z0-9_]+$') = Field(..., description="用户名")
    full_name: constr(min_length=2, max_length=100) = Field(..., description="真实姓名")
    password: constr(min_length=8, max_length=128) = Field(..., description="密码")
    phone: Optional[constr(regex=r'^\+?1?\d{9,15}$')] = Field(None, description="手机号码")

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        if v.startswith('_') or v.endswith('_'):
            raise ValueError('用户名不能以下划线开头或结尾')
        return v

    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not re.search(r'[a-z]', v):
            raise ValueError('密码必须包含小写字母')
        if not re.search(r'[A-Z]', v):
            raise ValueError('密码必须包含大写字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含数字')
        return v


class UserUpdateValidator(BaseValidator):
    """用户更新验证"""
    full_name: Optional[constr(min_length=2, max_length=100)] = Field(None, description="真实姓名")
    phone: Optional[constr(regex=r'^\+?1?\d{9,15}$')] = Field(None, description="手机号码")
    avatar_url: Optional[HttpUrl] = Field(None, description="头像URL")
    bio: Optional[constr(max_length=500)] = Field(None, description="个人简介")
    department: Optional[constr(max_length=100)] = Field(None, description="部门")
    position: Optional[constr(max_length=100)] = Field(None, description="职位")


class UserRolesValidator(BaseValidator):
    """用户角色验证"""
    roles: List[constr(regex=r'^(tenant_admin|hr_manager|hr_specialist|recruiter|interviewer|system_admin|support)$')] = Field(
        ..., description="用户角色列表"
    )

    @validator('roles')
    def validate_roles(cls, v):
        if len(v) == 0:
            raise ValueError('用户至少需要一个角色')

        # 检查角色冲突
        if 'system_admin' in v and len(v) > 1:
            raise ValueError('系统管理员不能有其他角色')

        return v


# 搜索和过滤验证器
class SearchValidator(BaseValidator):
    """搜索参数验证"""
    keyword: Optional[constr(max_length=100)] = Field(None, description="搜索关键词")
    page: int = Field(1, ge=1, le=1000, description="页码")
    pageSize: int = Field(10, ge=1, le=100, description="每页数量")
    sort_by: Optional[constr(max_length=50)] = Field(None, description="排序字段")
    sort_order: Optional[constr(regex=r'^(asc|desc)$')] = Field('desc', description="排序方向")

    @validator('keyword')
    def sanitize_keyword(cls, v):
        if v:
            # 移除潜在的SQL注入字符
            v = re.sub(r"[;\"'()=<>]", "", v)
            if len(v.strip()) < 2:
                raise ValueError('搜索关键词至少需要2个字符')
        return v.strip()


class DateRangeFilterValidator(BaseValidator):
    """日期范围过滤验证"""
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v is not None and 'start_date' in values and values['start_date'] is not None:
            if v < values['start_date']:
                raise ValueError('结束日期不能早于开始日期')
        return v


# 验证工具函数
def validate_and_sanitize(data: Dict[str, Any], validator_class: type) -> Dict[str, Any]:
    """
    验证和清理数据

    Args:
        data: 原始数据
        validator_class: 验证器类

    Returns:
        验证后的数据

    Raises:
        ValidationError: 验证失败
    """
    try:
        validated_data = validator_class(**data)
        return validated_data.dict(exclude_unset=True)
    except ValidationError as e:
        # 记录验证错误
        import structlog
        logger = structlog.get_logger(__name__)
        logger.warning("Data validation failed", errors=e.errors(), data=data)
        raise


def batch_validate(data_list: List[Dict[str, Any]], validator_class: type) -> List[Dict[str, Any]]:
    """
    批量验证数据

    Args:
        data_list: 数据列表
        validator_class: 验证器类

    Returns:
        验证后的数据列表

    Raises:
        ValidationError: 任何一个验证失败
    """
    results = []
    errors = []

    for i, data in enumerate(data_list):
        try:
            validated_data = validator_class(**data)
            results.append(validated_data.dict(exclude_unset=True))
        except ValidationError as e:
            errors.append(f"Item {i}: {e}")

    if errors:
        raise ValidationError(f"Batch validation failed: {'; '.join(errors)}")

    return results