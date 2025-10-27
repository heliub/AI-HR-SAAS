"""
User schemas
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_serializer
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
    lastLoginAt: Optional[str] = Field(alias="last_login_at")


class ProfileUpdateRequest(BaseModel):
    """个人信息更新请求"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None


class PasswordUpdateRequest(BaseModel):
    """密码更新请求"""
    currentPassword: str
    newPassword: str = Field(..., min_length=8)


class NotificationSettingsRequest(BaseModel):
    """通知设置请求"""
    emailNotifications: bool
    taskReminders: bool

