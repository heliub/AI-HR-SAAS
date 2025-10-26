"""
Channel endpoints
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.channel import ChannelCreate, ChannelUpdate, ChannelResponse, ChannelSyncResponse
from app.schemas.base import APIResponse, PaginatedResponse
from app.models.user import User

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_channels(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取渠道列表"""
    # TODO: 实现渠道列表查询
    return APIResponse(
        code=200,
        message="成功",
        data={"list": [], "total": 0, "page": page, "pageSize": pageSize}
    )


@router.post("", response_model=APIResponse)
async def create_channel(
    channel_data: ChannelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建渠道"""
    # TODO: 实现渠道创建
    return APIResponse(
        code=200,
        message="渠道创建成功"
    )


@router.put("/{channel_id}", response_model=APIResponse)
async def update_channel(
    channel_id: UUID,
    channel_data: ChannelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新渠道"""
    # TODO: 实现渠道更新
    return APIResponse(
        code=200,
        message="渠道更新成功"
    )


@router.delete("/{channel_id}", response_model=APIResponse)
async def delete_channel(
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除渠道"""
    # TODO: 实现渠道删除
    return APIResponse(
        code=200,
        message="渠道删除成功"
    )


@router.post("/{channel_id}/sync", response_model=APIResponse)
async def sync_channel(
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """同步渠道数据"""
    # TODO: 实现渠道同步
    from datetime import datetime
    sync_result = ChannelSyncResponse(
        newResumes=5,
        syncedAt=datetime.utcnow()
    )
    return APIResponse(
        code=200,
        message="同步成功",
        data=sync_result.model_dump()
    )

