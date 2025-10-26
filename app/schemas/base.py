"""
Base schemas
"""
from datetime import datetime
from typing import Optional, Any
from uuid import UUID
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
    id: UUID


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = 1
    pageSize: int = 10


class PaginatedResponse(BaseModel):
    """分页响应"""
    total: int
    page: int
    pageSize: int
    list: list[Any]


class APIResponse(BaseModel):
    """统一API响应格式"""
    code: int = 200
    message: str = "成功"
    data: Optional[Any] = None

