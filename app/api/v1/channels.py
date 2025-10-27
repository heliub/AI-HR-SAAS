"""
Channel endpoints
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.api.permissions import check_resource_permission, validate_pagination_params
from app.api.responses import (
    create_success_response, create_error_response,
    create_paginated_response, handle_service_error
)
from app.schemas.channel import ChannelCreate, ChannelUpdate, ChannelResponse, ChannelSyncResponse
from app.schemas.base import APIResponse, PaginatedResponse
from app.services.channel_service import ChannelService
from app.models.user import User

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_channels(
    page: int = Query(1, description="页码"),
    pageSize: int = Query(10, description="每页数量", ge=1, le=100),
    search: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="渠道状态"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取渠道列表"""
    # 验证分页参数
    page, pageSize = validate_pagination_params(page, pageSize)

    channel_service = ChannelService()

    # 判断是否为管理员
    is_admin = current_user.role == "admin"

    channels, total = await channel_service.get_channels(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        page=page,
        page_size=pageSize,
        search=search,
        status=status,
        is_admin=is_admin
    )

    channel_responses = [ChannelResponse.model_validate(channel) for channel in channels]

    return create_paginated_response(
        items=channel_responses,
        total=total,
        page=page,
        page_size=pageSize,
        message="获取渠道列表成功"
    )


@router.post("", response_model=APIResponse)
async def create_channel(
    channel_data: ChannelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建渠道"""
    channel_service = ChannelService()

    try:
        channel = await channel_service.create_channel(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            **channel_data.model_dump(exclude_unset=True)
        )

        channel_response = ChannelResponse.model_validate(channel)

        return create_success_response(
            message="渠道创建成功",
            data=channel_response.model_dump()
        )
    except Exception as e:
        return handle_service_error(e, "创建渠道")


@router.put("/{channel_id}", response_model=APIResponse)
async def update_channel(
    channel_id: UUID,
    channel_data: ChannelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新渠道"""
    channel_service = ChannelService()

    # 使用权限装饰器检查权限
    @check_resource_permission(channel_service, check_tenant=True, check_user=True)
    async def _update_channel():
        channel = await channel_service.update_channel(
            db=db,
            channel_id=channel_id,
            **channel_data.model_dump(exclude_unset=True)
        )
        return channel

    try:
        channel = await _update_channel()
        channel_response = ChannelResponse.model_validate(channel)

        return APIResponse(
            code=200,
            message="渠道更新成功",
            data=channel_response.model_dump()
        )
    except HTTPException as e:
        return APIResponse(
            code=e.status_code,
            message=e.detail
        )


@router.delete("/{channel_id}", response_model=APIResponse)
async def delete_channel(
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除渠道"""
    channel_service = ChannelService()

    # 检查渠道是否存在
    channel = await channel_service.get(db, channel_id)
    if not channel or channel.tenant_id != current_user.tenant_id or channel.user_id != current_user.id:
        return APIResponse(
            code=404,
            message="渠道不存在"
        )

    await channel_service.delete(db, channel_id)

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
    channel_service = ChannelService()

    # 检查渠道是否存在
    channel = await channel_service.get(db, channel_id)
    if not channel or channel.tenant_id != current_user.tenant_id or channel.user_id != current_user.id:
        return APIResponse(
            code=404,
            message="渠道不存在"
        )

    sync_result = await channel_service.sync_channel(db, channel_id)

    return APIResponse(
        code=200,
        message="同步成功",
        data=sync_result
    )

