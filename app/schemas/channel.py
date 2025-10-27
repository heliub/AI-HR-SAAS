"""
Channel schemas
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field, field_serializer
from app.schemas.base import BaseSchema, TimestampSchema, IDSchema
from app.utils.datetime_formatter import format_datetime


class ChannelBase(BaseModel):
    """渠道基础Schema"""
    name: str = Field(..., min_length=1, max_length=100)
    type: str
    status: str = "active"
    cost: Optional[str] = None
    apiKey: Optional[str] = None
    contactPerson: Optional[str] = None
    contactEmail: Optional[EmailStr] = None
    description: Optional[str] = None


class ChannelCreate(ChannelBase):
    """创建渠道"""
    pass


class ChannelUpdate(BaseModel):
    """更新渠道"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = None
    status: Optional[str] = None
    cost: Optional[str] = None
    apiKey: Optional[str] = None
    contactPerson: Optional[str] = None
    contactEmail: Optional[EmailStr] = None
    description: Optional[str] = None


class ChannelResponse(ChannelBase, IDSchema, TimestampSchema):
    """渠道响应"""
    userId: Optional[UUID] = Field(alias="user_id")
    applicantsCount: int = Field(alias="applicants_count")
    lastSync: Optional[datetime] = Field(None, alias="last_sync_at")

    @field_serializer('lastSync')
    def serialize_last_sync(self, value: Optional[datetime]) -> Optional[str]:
        """格式化最后同步时间为可读格式"""
        return format_datetime(value)


class ChannelSyncResponse(BaseModel):
    """渠道同步响应"""
    newResumes: int
    syncedAt: datetime

    @field_serializer('syncedAt')
    def serialize_synced_at(self, value: datetime) -> str:
        """格式化同步时间为可读格式"""
        return format_datetime(value)

