"""
Statistics endpoints
"""
from typing import Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.stats import (
    DashboardStats, JobStats, ResumeStats,
    ChannelStats, FunnelStats, ConversionRates
)
from app.schemas.base import APIResponse
from app.services.stats_service import StatsService
from app.models.user import User

router = APIRouter()


@router.get("/dashboard", response_model=APIResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取Dashboard统计数据"""
    stats_service = StatsService()

    stats_data = await stats_service.get_dashboard_stats(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )

    return APIResponse(
        code=200,
        message="成功",
        data=stats_data
    )


@router.get("/jobs", response_model=APIResponse)
async def get_job_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取职位统计数据"""
    stats_service = StatsService()

    stats_data = await stats_service.get_job_stats(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )

    return APIResponse(
        code=200,
        message="成功",
        data=stats_data
    )


@router.get("/resumes", response_model=APIResponse)
async def get_resume_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取简历统计数据"""
    stats_service = StatsService()

    stats_data = await stats_service.get_resume_stats(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )

    return APIResponse(
        code=200,
        message="成功",
        data=stats_data
    )


@router.get("/channels", response_model=APIResponse)
async def get_channel_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取渠道统计数据"""
    stats_service = StatsService()

    stats_data = await stats_service.get_channel_stats(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )

    return APIResponse(
        code=200,
        message="成功",
        data=stats_data
    )


@router.get("/funnel", response_model=APIResponse)
async def get_funnel_stats(
    startDate: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    endDate: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取招聘漏斗数据"""
    stats_service = StatsService()

    # 转换日期字符串为datetime对象，添加异常处理
    start_dt = None
    end_dt = None
    if startDate:
        try:
            start_dt = datetime.fromisoformat(startDate)
        except ValueError:
            raise HTTPException(status_code=400, detail="开始日期格式无效，请使用YYYY-MM-DD格式")
    if endDate:
        try:
            end_dt = datetime.fromisoformat(endDate)
        except ValueError:
            raise HTTPException(status_code=400, detail="结束日期格式无效，请使用YYYY-MM-DD格式")

    # 验证日期范围
    if start_dt and end_dt and start_dt > end_dt:
        raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")

    stats_data = await stats_service.get_funnel_stats(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        start_date=start_dt,
        end_date=end_dt
    )

    return APIResponse(
        code=200,
        message="成功",
        data=stats_data
    )

