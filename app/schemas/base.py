"""
Base schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """基础Schema"""
    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(BaseSchema):
    """时间戳Schema"""
    created_at: datetime
    updated_at: datetime


class IDSchema(BaseSchema):
    """ID Schema"""
    id: int


class PaginationParams(BaseModel):
    """分页参数"""
    skip: int = 0
    limit: int = 100


class PaginatedResponse(BaseModel):
    """分页响应"""
    total: int
    skip: int
    limit: int
    items: list


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    code: Optional[str] = None
    details: Optional[dict] = None

