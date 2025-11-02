"""
Base schemas
"""
from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utils.datetime_formatter import format_datetime


class BaseSchema(BaseModel):
    """基础Schema"""
    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(BaseSchema):
    """时间戳Schema - 数据库用snake_case，API用camelCase"""
    createdAt: Optional[datetime] = Field(alias="created_at")
    updatedAt: Optional[datetime] = Field(alias="updated_at")

    @field_serializer('createdAt', 'updatedAt', when_used='always')
    def serialize_timestamps(self, value: Optional[datetime]) -> Optional[str]:
        """序列化时间戳"""
        if value is None:
            return None
        return format_datetime(value)


class IDSchema(BaseSchema):
    """ID Schema"""
    id: UUID


class PaginationParams(BaseModel):
    """分页参数 - 统一使用camelCase面向API"""
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

class ListResponse(BaseModel):
    """分页响应"""
    total: int
    list: list[Any]