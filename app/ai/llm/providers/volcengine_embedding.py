"""
Volcengine (火山引擎) Embedding Provider

支持火山引擎 Embedding API
"""
import asyncio
from typing import Any, Dict, List

from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError, AuthenticationError

from app.ai.llm.base import BaseEmbeddingClient
from app.ai.llm.types import EmbeddingRequest, EmbeddingResponse, EmbeddingData, EmbeddingUsage
from app.ai.llm.errors import (
    LLMError,
    LLMAPIError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
)


class VolcengineEmbeddingClient(BaseEmbeddingClient):
    """火山引擎 Embedding 客户端"""

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        super().__init__(api_key, base_url, timeout, max_retries)
        # 火山引擎兼容 OpenAI 格式
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=0,  # 手动控制重试
        )

    @property
    def provider_name(self) -> str:
        return "volcengine"

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """指数退避重试"""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except (APITimeoutError, RateLimitError, APIError) as e:
                last_error = e
                # 5xx错误或超时、限流才重试
                if isinstance(e, RateLimitError) or isinstance(e, APITimeoutError):
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt  # 1s, 2s, 4s
                        await asyncio.sleep(wait_time)
                        continue
                elif isinstance(e, APIError):
                    # 5xx错误重试
                    if hasattr(e, "status_code") and 500 <= e.status_code < 600:
                        if attempt < self.max_retries - 1:
                            wait_time = 2 ** attempt
                            await asyncio.sleep(wait_time)
                            continue
                raise
            except Exception:
                # 其他错误不重试
                raise

        # 重试耗尽，抛出最后一个错误
        raise last_error

    def _convert_error(self, error: Exception) -> LLMError:
        """转换错误为统一格式"""
        if isinstance(error, AuthenticationError):
            return LLMAuthenticationError(
                message=str(error),
                provider=self.provider_name,
                original_error=error,
            )
        elif isinstance(error, RateLimitError):
            return LLMRateLimitError(
                message=str(error),
                provider=self.provider_name,
                original_error=error,
            )
        elif isinstance(error, APITimeoutError):
            return LLMTimeoutError(
                message=str(error),
                timeout=self.timeout,
                provider=self.provider_name,
                original_error=error,
            )
        elif isinstance(error, APIError):
            status_code = getattr(error, "status_code", None)
            return LLMAPIError(
                message=str(error),
                status_code=status_code,
                provider=self.provider_name,
                original_error=error,
            )
        else:
            return LLMError(
                message=str(error),
                provider=self.provider_name,
                original_error=error,
            )

    async def create_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """创建 embedding"""
        try:
            # 构建请求参数
            params: Dict[str, Any] = {
                "model": request.model,
                "input": request.input,
            }

            if request.encoding_format:
                params["encoding_format"] = request.encoding_format

            # 带重试的请求
            response = await self._retry_with_backoff(
                self.client.embeddings.create,
                **params,
            )

            # 转换为统一格式
            embedding_data = [
                EmbeddingData(
                    embedding=item.embedding,
                    index=item.index,
                    object=getattr(item, "object", "embedding"),
                )
                for item in response.data
            ]

            usage = EmbeddingUsage(
                prompt_tokens=response.usage.prompt_tokens,
                total_tokens=response.usage.total_tokens,
            )

            return EmbeddingResponse(
                data=embedding_data,
                model=response.model,
                usage=usage,
                object=getattr(response, "object", "list"),
            )

        except Exception as e:
            raise self._convert_error(e)
