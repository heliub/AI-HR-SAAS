"""
统一API响应格式模块
"""
from typing import Any, Optional, Union
from fastapi import HTTPException
from pydantic import BaseModel

from app.schemas.base import APIResponse, PaginatedResponse


def create_success_response(
    message: str = "成功",
    data: Optional[Any] = None,
    code: int = 200
) -> APIResponse:
    """
    创建成功响应

    Args:
        message: 响应消息
        data: 响应数据
        code: 响应码

    Returns:
        APIResponse: 统一格式的成功响应
    """
    return APIResponse(
        code=code,
        message=message,
        data=data
    )


def create_error_response(
    message: str,
    code: int = 400,
    data: Optional[Any] = None
) -> APIResponse:
    """
    创建错误响应

    Args:
        message: 错误消息
        code: 错误码
        data: 额外错误数据

    Returns:
        APIResponse: 统一格式的错误响应
    """
    return APIResponse(
        code=code,
        message=message,
        data=data
    )


def create_paginated_response(
    list: list[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "成功"
) -> APIResponse:
    """
    创建分页响应

    Args:
        items: 数据项列表
        total: 总数
        page: 当前页码
        page_size: 每页数量
        message: 响应消息

    Returns:
        APIResponse: 统一格式的分页响应
    """
    paginated_data = PaginatedResponse(
        total=total,
        page=page,
        pageSize=page_size,
        list=list
    )

    return APIResponse(
        code=200,
        message=message,
        data=paginated_data.model_dump()
    )


def create_not_found_response(resource_name: str = "资源") -> APIResponse:
    """
    创建资源不存在响应

    Args:
        resource_name: 资源名称

    Returns:
        APIResponse: 资源不存在响应
    """
    return create_error_response(
        message=f"{resource_name}不存在",
        code=404
    )


def create_permission_denied_response(message: str = "无权限访问该资源") -> APIResponse:
    """
    创建权限拒绝响应

    Args:
        message: 错误消息

    Returns:
        APIResponse: 权限拒绝响应
    """
    return create_error_response(
        message=message,
        code=403
    )


def create_validation_error_response(field: str, reason: str) -> APIResponse:
    """
    创建参数验证错误响应

    Args:
        field: 字段名
        reason: 错误原因

    Returns:
        APIResponse: 参数验证错误响应
    """
    return create_error_response(
        message=f"参数验证失败: {field} - {reason}",
        code=422
    )


def handle_service_error(e: Exception, operation: str = "操作") -> APIResponse:
    """
    处理服务层异常

    Args:
        e: 异常对象
        operation: 操作名称

    Returns:
        APIResponse: 错误响应
    """
    error_message = f"{operation}失败"

    if isinstance(e, HTTPException):
        return create_error_response(
            message=e.detail,
            code=e.status_code
        )

    # 根据异常类型返回不同的错误信息
    if "permission" in str(e).lower():
        return create_permission_denied_response()

    if "not found" in str(e).lower() or "不存在" in str(e):
        return create_not_found_response()

    # 记录详细错误（在生产环境中）
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"{operation}失败: {str(e)}", exc_info=True)

    return create_error_response(
        message=error_message,
        code=500
    )


def validate_response_data(data: Any, schema_class: BaseModel) -> Any:
    """
    验证响应数据格式

    Args:
        data: 原始数据
        schema_class: Pydantic模型类

    Returns:
        Any: 验证后的数据
    """
    try:
        if isinstance(data, list):
            return [schema_class.model_validate(item).model_dump() for item in data]
        else:
            return schema_class.model_validate(data).model_dump()
    except Exception as e:
        raise ValueError(f"响应数据格式验证失败: {str(e)}")


class ResponseBuilder:
    """
    响应构建器类，提供链式调用接口
    """

    def __init__(self):
        self._code = 200
        self._message = "成功"
        self._data = None

    def success(self, message: str = "成功") -> "ResponseBuilder":
        """设置成功消息"""
        self._code = 200
        self._message = message
        return self

    def error(self, message: str, code: int = 400) -> "ResponseBuilder":
        """设置错误信息"""
        self._code = code
        self._message = message
        return self

    def data(self, data: Any) -> "ResponseBuilder":
        """设置响应数据"""
        self._data = data
        return self

    def not_found(self, resource_name: str = "资源") -> "ResponseBuilder":
        """设置为资源不存在"""
        return self.error(f"{resource_name}不存在", 404)

    def permission_denied(self, message: str = "无权限访问该资源") -> "ResponseBuilder":
        """设置为权限拒绝"""
        return self.error(message, 403)

    def build(self) -> APIResponse:
        """构建最终响应"""
        return APIResponse(
            code=self._code,
            message=self._message,
            data=self._data
        )


def response_builder() -> ResponseBuilder:
    """
    创建响应构建器实例

    Returns:
        ResponseBuilder: 响应构建器
    """
    return ResponseBuilder()