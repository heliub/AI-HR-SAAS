"""
LLM客户端抽象基类

定义统一的接口，所有provider必须实现
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator,List
from app.ai.llm.types import LLMRequest, LLMResponse, StreamChunk, EmbeddingRequest, EmbeddingResponse


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

class BaseEmbeddingClient(ABC):
    """Embedding 客户端抽象基类"""

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        """
        初始化 Embedding 客户端

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
    async def create_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        创建 embedding

        Args:
            request: Embedding 请求

        Returns:
            Embedding 响应

        Raises:
            LLMError: 调用错误
        """
        pass

    async def embed_text(self, text: str, model: str) -> List[float]:
        """
        便捷方法：为单个文本生成 embedding

        Args:
            text: 输入文本
            model: 模型名称

        Returns:
            Embedding 向量
        """
        request = EmbeddingRequest(model=model, input=text)
        response = await self.create_embedding(request)
        return response.data[0].embedding

    async def embed_texts(self, texts: List[str], model: str) -> List[List[float]]:
        """
        便捷方法：为多个文本生成 embedding

        Args:
            texts: 文本列表
            model: 模型名称

        Returns:
            Embedding 向量列表
        """
        request = EmbeddingRequest(model=model, input=texts)
        response = await self.create_embedding(request)
        # 按 index 排序，确保顺序正确
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """provider 名称"""
        pass
