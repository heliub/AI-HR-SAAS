"""
LLM错误定义

统一封装不同厂商的错误，保留原始错误信息
"""
from typing import Optional, Any


class LLMError(Exception):
    """LLM错误基类"""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        self.message = message
        self.provider = provider
        self.original_error = original_error
        super().__init__(message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.provider:
            parts.append(f"[provider={self.provider}]")
        if self.original_error:
            parts.append(f"[original={type(self.original_error).__name__}: {self.original_error}]")
        return " ".join(parts)


class LLMAPIError(LLMError):
    """API调用错误"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        provider: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        self.status_code = status_code
        super().__init__(message, provider, original_error)

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"[status={self.status_code}]")
        if self.provider:
            parts.append(f"[provider={self.provider}]")
        if self.original_error:
            parts.append(f"[original={type(self.original_error).__name__}]")
        return " ".join(parts)


class LLMTimeoutError(LLMError):
    """超时错误"""

    def __init__(
        self,
        message: str = "LLM request timeout",
        timeout: Optional[float] = None,
        provider: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        self.timeout = timeout
        super().__init__(message, provider, original_error)


class LLMRateLimitError(LLMAPIError):
    """限流错误"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        provider: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        self.retry_after = retry_after
        super().__init__(message, status_code=429, provider=provider, original_error=original_error)


class LLMAuthenticationError(LLMAPIError):
    """认证错误"""

    def __init__(
        self,
        message: str = "Authentication failed",
        provider: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, status_code=401, provider=provider, original_error=original_error)


class LLMValidationError(LLMError):
    """参数验证错误"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        provider: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        self.field = field
        super().__init__(message, provider, original_error)
