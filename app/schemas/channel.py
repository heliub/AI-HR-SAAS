"""
Channel schemas
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field
from app.schemas.base import BaseSchema, TimestampSchema, IDSchema


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
    userId: Optional[UUID] = Field(None, alias="user_id", serialization_alias="userId")
    applicants: int = 0
    lastSync: Optional[datetime] = None


class ChannelSyncResponse(BaseModel):
    """渠道同步响应"""
    newResumes: int
    syncedAt: datetime

