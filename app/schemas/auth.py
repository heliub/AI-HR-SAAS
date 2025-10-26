"""
Authentication schemas
"""
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserInfo(BaseModel):
    """用户信息"""
    id: UUID
    name: str
    email: EmailStr
    role: str
    avatar: Optional[str] = None


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    user: UserInfo


class LogoutRequest(BaseModel):
    """登出请求"""
    token: str


class TokenPayload(BaseModel):
    """Token载荷"""
    sub: UUID  # user_id
    tenant_id: UUID
    role: str

