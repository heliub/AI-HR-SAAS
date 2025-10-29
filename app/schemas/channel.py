"""
Channel schemas
"""
from typing import Optional, Union
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field, field_serializer, ConfigDict
from app.schemas.base import BaseSchema, TimestampSchema, IDSchema
from app.utils.datetime_formatter import format_datetime
import re


class ChannelBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    """渠道基础Schema"""
    name: str = Field(..., min_length=1, max_length=100)
    status: str = "active"
    cost: Optional[str] = Field(None, alias="annual_cost")
    costCurrency: Optional[str] = Field("CNY", alias="cost_currency")
    apiKey: Optional[str] = Field(None, alias="api_key")
    contactPerson: Optional[str] = Field(None, alias="contact_person")
    contactEmail: Optional[Union[EmailStr, str]] = Field(None, alias="contact_email")
    description: Optional[str] = None

    @field_serializer('contactEmail')
    def serialize_contact_email(self, value: Optional[Union[EmailStr, str]]) -> Optional[str]:
        """序列化联系邮箱，如果为 EmailStr 则转换为字符串"""
        if isinstance(value, EmailStr):
            return str(value)
        return value


class ChannelCreate(ChannelBase):
    """创建渠道"""
    pass


class ChannelUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    """更新渠道"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = None
    status: Optional[str] = None
    cost: Optional[str] = Field(None, alias="annual_cost")
    costCurrency: Optional[str] = Field(None, alias="cost_currency")
    apiKey: Optional[str] = Field(None, alias="api_key")
    contactPerson: Optional[str] = Field(None, alias="contact_person")
    contactEmail: Optional[Union[EmailStr, str]] = Field(None, alias="contact_email")
    description: Optional[str] = None


class ChannelResponse(BaseModel):
    """渠道响应"""
    # 基础字段
    id: Optional[UUID] = None
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    cost: Optional[Union[Decimal, str]] = Field(None, alias="annual_cost")
    costCurrency: Optional[str] = Field(None, alias="cost_currency")
    # apiKey: Optional[str] = Field(None, alias="api_key")
    contactPerson: Optional[str] = Field(None, alias="contact_person")
    contactEmail: Optional[Union[EmailStr, str]] = Field(None, alias="contact_email")
    description: Optional[str] = Field(None, alias="description")
    
    # 关联字段
    userId: Optional[UUID] = Field(alias="user_id")
    applicantsCount: int = Field(alias="applicants_count")
    lastSync: Optional[datetime] = Field(None, alias="last_sync_at")
    createdAt: Optional[datetime] = Field(None, alias="created_at")
    updatedAt: Optional[datetime] = Field(None, alias="updated_at")

    @field_serializer('lastSync')
    def serialize_last_sync(self, value: Optional[datetime]) -> Optional[str]:
        """格式化最后同步时间为可读格式"""
        return format_datetime(value)
    
    @field_serializer('cost', when_used='always')
    def serialize_cost(self, value: Optional[Union[Decimal, str]]) -> Optional[str]:
        """序列化成本为字符串"""
        if value is not None:
            return str(value)
        return None
    
    @field_serializer('contactEmail', when_used='always')
    def serialize_contact_email(self, value: Optional[Union[EmailStr, str]]) -> Optional[str]:
        """序列化联系邮箱，如果为 EmailStr 则转换为字符串"""
        if isinstance(value, EmailStr):
            return str(value)
        return value
    
    @field_serializer('createdAt', when_used='always')
    def serialize_created_at(self, value: Optional[datetime]) -> Optional[str]:
        """格式化创建时间为可读格式"""
        return format_datetime(value)
    
    @field_serializer('updatedAt', when_used='always')
    def serialize_updated_at(self, value: Optional[datetime]) -> Optional[str]:
        """格式化更新时间为可读格式"""
        return format_datetime(value)


class ChannelStatusUpdate(BaseModel):
    """渠道状态更新"""
    status: str = Field(..., description="渠道状态: active, inactive, deleted")


class ChannelSyncResponse(BaseModel):
    """渠道同步响应"""
    newResumes: int
    syncedAt: datetime

    @field_serializer('syncedAt')
    def serialize_synced_at(self, value: datetime) -> str:
        """格式化同步时间为可读格式"""
        return format_datetime(value)

