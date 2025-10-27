"""
权限校验模块
"""
from functools import wraps
from typing import Any, Callable
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


def check_resource_permission(
    resource_service: Any,
    check_tenant: bool = True,
    check_user: bool = False
):
    """
    资源权限校验装饰器

    Args:
        resource_service: 资源服务实例
        check_tenant: 是否检查租户权限
        check_user: 是否检查用户权限
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取参数
            resource_id = None
            db = None
            current_user = None

            # 从kwargs中提取关键参数
            for key, value in kwargs.items():
                if key.endswith('_id') and isinstance(value, UUID):
                    resource_id = value
                elif key == 'db':
                    db = value
                elif key == 'current_user':
                    current_user = value

            if not all([resource_id, db, current_user]):
                raise HTTPException(status_code=500, detail="权限校验参数不完整")

            # 检查资源是否存在和权限
            try:
                resource = await resource_service.get(db, resource_id)
                if not resource:
                    raise HTTPException(status_code=404, detail="资源不存在")

                # 检查租户权限
                if check_tenant and resource.tenant_id != current_user.tenant_id:
                    raise HTTPException(status_code=403, detail="无权限访问该资源")

                # 检查用户权限
                if check_user and hasattr(resource, 'user_id') and resource.user_id != current_user.id:
                    raise HTTPException(status_code=403, detail="无权限访问该资源")

            except AttributeError:
                raise HTTPException(status_code=500, detail="权限校验配置错误")

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def validate_pagination_params(page: int = 1, page_size: int = 10) -> tuple[int, int]:
    """
    验证分页参数

    Args:
        page: 页码
        page_size: 每页数量

    Returns:
        tuple: (page, page_size)

    Raises:
        HTTPException: 参数无效时
    """
    if page < 1:
        raise HTTPException(status_code=400, detail="页码必须大于0")

    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="每页数量必须在1-100之间")

    return page, page_size


def validate_uuid_param(param_value: str, param_name: str = "ID") -> UUID:
    """
    验证UUID参数

    Args:
        param_value: 参数值
        param_name: 参数名称

    Returns:
        UUID: 转换后的UUID

    Raises:
        HTTPException: 参数无效时
    """
    try:
        return UUID(param_value)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"{param_name}格式无效")