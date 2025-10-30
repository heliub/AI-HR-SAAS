"""
LLM客户端抽象基类

定义统一的接口，所有provider必须实现
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator

from .types import LLMRequest, LLMResponse, StreamChunk


class BaseLLMClient(ABC):
    """LLM客户端抽象基类"""

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        """
        初始化LLM客户端

        Args:
            api_key: API密钥
            base_url: API base URL（可选）
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    async def chat(self, request: LLMRequest) -> LLMResponse:
        """
        非流式对话

        Args:
            request: LLM请求

        Returns:
            LLM响应

        Raises:
            LLMError: LLM调用错误
        """
        pass

    @abstractmethod
    async def stream_chat(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """
        流式对话

        Args:
            request: LLM请求

        Yields:
            流式响应块

        Raises:
            LLMError: LLM调用错误
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """provider名称"""
        pass
