"""
Authentication schemas
"""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    tenant_id: int
    username: str
    role: str


class TokenPayload(BaseModel):
    """Token载荷"""
    sub: int  # user_id
    tenant_id: int
    role: str

