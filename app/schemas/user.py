"""
User schemas
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_serializer, ConfigDict
from app.schemas.base import BaseSchema, TimestampSchema, IDSchema
from app.utils.datetime_formatter import format_datetime


class UserBase(BaseModel):
    """用户基础Schema"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    role: str = "hr"


class UserCreate(UserBase):
    """创建用户"""
    password: str = Field(..., min_length=8)
    tenantId: UUID = Field(alias="tenant_id")


class UserUpdate(BaseModel):
    """更新用户"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[str] = None


class UserResponse(UserBase, IDSchema, TimestampSchema):

    """用户响应"""
    tenantId: UUID = Field(alias="tenant_id")
    avatarUrl: Optional[str] = Field(alias="avatar_url")
    isActive: bool = Field(alias="is_active")
    lastLoginAt: Optional[datetime] = Field(alias="last_login_at", default=None)

    @field_serializer('lastLoginAt', when_used='always')
    def serialize_last_login_at(self, value: Optional[datetime]) -> Optional[str]:
        """序列化最后登录时间"""
        if value is None:
            return None
        return format_datetime(value)


class ProfileUpdateRequest(BaseModel):
    """个人信息更新请求（不包含角色字段）"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None


class PasswordUpdateRequest(BaseModel):
    """密码更新请求"""
    currentPassword: str
    newPassword: str = Field(..., min_length=8)

class UserSettingRequest(BaseModel):
    """用户设置请求"""
    language: Optional[str] = Field(None, pattern="^(zh|en|id)$")
    emailNotifications: Optional[bool] = Field(None, alias="email_notifications")
    taskReminders: Optional[bool] = Field(None, alias="task_reminders")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserSettingResponse(BaseModel):
    """用户设置响应"""
    language: str
    emailNotifications: bool = Field(alias="email_notifications")
    taskReminders: bool = Field(alias="task_reminders")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, by_alias=True)

