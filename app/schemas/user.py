"""
User schemas
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.base import BaseSchema, TimestampSchema, IDSchema


class UserBase(BaseModel):
    """用户基础Schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    language: str = "en"
    role: str = "hr"


class UserCreate(UserBase):
    """创建用户"""
    password: str = Field(..., min_length=8)
    tenant_id: int


class UserUpdate(BaseModel):
    """更新用户"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    language: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase, IDSchema, TimestampSchema):
    """用户响应"""
    tenant_id: int
    status: str
    last_login_at: Optional[str] = None


class UserListResponse(BaseModel):
    """用户列表响应"""
    users: list[UserResponse]
    total: int

