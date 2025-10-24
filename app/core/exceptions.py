"""
Custom exceptions
"""
from typing import Any, Optional


class AppException(Exception):
    """应用基础异常"""
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: int = 500,
        details: Optional[Any] = None,
    ):
        self.message = message
        self.code = code or "INTERNAL_ERROR"
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class NotFoundException(AppException):
    """资源不存在异常"""
    
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details,
        )


class UnauthorizedException(AppException):
    """未授权异常"""
    
    def __init__(self, message: str = "Unauthorized", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
            details=details,
        )


class ForbiddenException(AppException):
    """禁止访问异常"""
    
    def __init__(self, message: str = "Forbidden", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            details=details,
        )


class BadRequestException(AppException):
    """错误请求异常"""
    
    def __init__(self, message: str = "Bad request", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="BAD_REQUEST",
            status_code=400,
            details=details,
        )


class ConflictException(AppException):
    """冲突异常"""
    
    def __init__(self, message: str = "Resource conflict", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details,
        )


class ValidationException(AppException):
    """验证异常"""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class TenantNotFoundException(NotFoundException):
    """租户不存在异常"""
    
    def __init__(self, tenant_id: int):
        super().__init__(
            message=f"Tenant {tenant_id} not found",
            details={"tenant_id": tenant_id},
        )


class UserNotFoundException(NotFoundException):
    """用户不存在异常"""
    
    def __init__(self, user_id: int):
        super().__init__(
            message=f"User {user_id} not found",
            details={"user_id": user_id},
        )


class AIServiceException(AppException):
    """AI服务异常"""
    
    def __init__(self, message: str = "AI service error", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="AI_SERVICE_ERROR",
            status_code=500,
            details=details,
        )


class RPAException(AppException):
    """RPA异常"""
    
    def __init__(self, message: str = "RPA operation failed", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="RPA_ERROR",
            status_code=500,
            details=details,
        )


class RateLimitException(AppException):
    """速率限制异常"""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details,
        )

