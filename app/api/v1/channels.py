"""
Channel endpoints
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.api.deps import get_db, get_current_user
from app.api.permissions import check_resource_permission, validate_pagination_params
from app.api.responses import (
    create_success_response, create_error_response,
    create_paginated_response, handle_service_error
)
from app.schemas.channel import ChannelCreate, ChannelUpdate, ChannelResponse, ChannelSyncResponse, ChannelStatusUpdate
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

    channel_responses = [ChannelResponse.model_validate(channel, from_attributes=True) for channel in channels]

    return create_paginated_response(
        list=channel_responses,
        total=total,
        page=page,
        page_size=pageSize
    )


@router.post("/create", response_model=APIResponse)
async def create_channel(
    channel_data: ChannelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建渠道"""
    channel_service = ChannelService()

    try:
        # 转换数据，处理 cost 字段
        data = channel_data.model_dump(by_alias=True, exclude_unset=True)
        
        channel = await channel_service.create_channel(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            **data
        )

        channel_response = ChannelResponse.model_validate(channel, from_attributes=True)

        return create_success_response(
            message="渠道创建成功",
            data=channel_response.model_dump()
        )
    except Exception as e:
        return handle_service_error(e, "创建渠道")


@router.put("/{channel_id}", response_model=APIResponse)
@check_resource_permission(ChannelService(), check_tenant=True, check_user=True)
async def update_channel(
    channel_id: UUID,
    channel_data: ChannelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新渠道"""
    channel_service = ChannelService()

    # 获取渠道并检查是否已删除（装饰器已经检查了存在性和权限）
    channel = await channel_service.get(db, channel_id)
    if channel.status == "deleted":
        return APIResponse(
            code=404,
            message="渠道不存在"
        )

    try:
        # 转换数据，处理 cost 字段
        data = channel_data.model_dump(by_alias=True, exclude_unset=True)

        if 'annual_cost' in data and data['annual_cost'] is not None:
            # 将字符串形式的 cost 转换为 Decimal
            data['annual_cost'] = Decimal(str(data['annual_cost']))

        channel = await channel_service.update_channel(
            db=db,
            channel_id=channel_id,
            **data
        )

        channel_response = ChannelResponse.model_validate(channel, from_attributes=True)
        

        return APIResponse(
            code=200,
            message="渠道更新成功",
            data=channel_response.model_dump()
        )
    except Exception as e:
        return handle_service_error(e, "更新渠道")


@router.delete("/{channel_id}", response_model=APIResponse)
async def delete_channel(
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除渠道（逻辑删除）"""
    channel_service = ChannelService()

    # 检查渠道是否存在
    channel = await channel_service.get(db, channel_id)
    if not channel or channel.tenant_id != current_user.tenant_id or channel.user_id != current_user.id:
        return APIResponse(
            code=404,
            message="渠道不存在"
        )

    # 逻辑删除渠道
    await channel_service.delete_channel(db, channel_id)

    return APIResponse(
        code=200,
        message="渠道删除成功"
    )


@router.get("/{channel_id}", response_model=APIResponse)
async def get_channel(
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取渠道详情"""
    channel_service = ChannelService()

    # 检查渠道是否存在
    channel = await channel_service.get(db, channel_id)
    if not channel or channel.tenant_id != current_user.tenant_id or channel.status == "deleted":
        return APIResponse(
            code=404,
            message="渠道不存在"
        )

    # 非管理员用户只能查看自己创建的渠道
    if current_user.role != "admin" and channel.user_id != current_user.id:
        return APIResponse(
            code=403,
            message="无权访问该渠道"
        )

    channel_response = ChannelResponse.model_validate(channel, from_attributes=True)

    return create_success_response(
        message="获取渠道详情成功",
        data=channel_response.model_dump()
    )


@router.patch("/{channel_id}/status", response_model=APIResponse)
async def update_channel_status(
    channel_id: UUID,
    status_update: ChannelStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新渠道状态"""
    channel_service = ChannelService()

    # 检查渠道是否存在
    channel = await channel_service.get(db, channel_id)
    if not channel or channel.tenant_id != current_user.tenant_id:
        return APIResponse(
            code=404,
            message="渠道不存在"
        )

    # 非管理员用户只能更新自己创建的渠道状态
    if current_user.role != "admin" and channel.user_id != current_user.id:
        return APIResponse(
            code=403,
            message="无权修改该渠道状态"
        )

    try:
        channel = await channel_service.update_channel_status(db, channel_id, status_update.status)
        channel_response = ChannelResponse.model_validate(channel, from_attributes=True)

        return create_success_response(
            message="渠道状态更新成功",
            data=channel_response.model_dump()
        )
    except ValueError as e:
        return APIResponse(
            code=400,
            message=str(e)
        )
    except Exception as e:
        return handle_service_error(e, "更新渠道状态")


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
    if not channel or channel.tenant_id != current_user.tenant_id or channel.user_id != current_user.id or channel.status == "deleted":
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

