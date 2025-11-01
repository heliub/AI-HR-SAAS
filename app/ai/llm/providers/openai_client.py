"""
OpenAI Provider

支持OpenAI官方API和兼容OpenAI格式的其他厂商
"""
import asyncio
from typing import AsyncIterator, Any, Dict, List
from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError, AuthenticationError

from ..base import BaseLLMClient
from ..types import LLMRequest, LLMResponse, StreamChunk, Message, Usage, ToolCall
from ..errors import (
    LLMError,
    LLMAPIError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
)


class OpenAIClient(BaseLLMClient):
    """OpenAI客户端"""

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        super().__init__(api_key, base_url, timeout, max_retries)
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=0,  # 手动控制重试
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    def _build_messages(self, request: LLMRequest) -> List[Dict[str, Any]]:
        """
        构建消息列表，自动处理system prompt

        Args:
            request: LLM请求

        Returns:
            消息列表
        """
        messages = []

        # 如果有system，插入到最前面
        if request.system:
            messages.append({"role": "system", "content": request.system})

        # 添加对话消息
        for msg in request.messages:
            msg_dict = {"role": msg.role}

            # content
            if msg.content is not None:
                msg_dict["content"] = msg.content

            # tool_calls (assistant调用工具)
            if msg.tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": tc.function,
                    }
                    for tc in msg.tool_calls
                ]

            # tool_call_id (tool角色返回结果)
            if msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id

            messages.append(msg_dict)

        return messages

    def _build_request_params(self, request: LLMRequest) -> Dict[str, Any]:
        """构建请求参数"""
        params = {
            "model": request.model,
            "messages": self._build_messages(request),
            "temperature": request.temperature,
            "stream": request.stream,
        }

        # 可选参数
        if request.max_tokens is not None:
            params["max_tokens"] = request.max_tokens
        if request.top_p is not None:
            params["top_p"] = request.top_p
        if request.frequency_penalty is not None:
            params["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty is not None:
            params["presence_penalty"] = request.presence_penalty
        if request.stop is not None:
            params["stop"] = request.stop
        if request.tools is not None:
            params["tools"] = request.tools
        if request.tool_choice is not None:
            params["tool_choice"] = request.tool_choice

        return params

    def _parse_message(self, choice: Any) -> Message:
        """解析响应消息"""
        msg = choice.message
        message = Message(role="assistant")

        # content
        if hasattr(msg, "content") and msg.content is not None:
            message.content = msg.content

        # tool_calls
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            message.tool_calls = [
                ToolCall(
                    id=tc.id,
                    type=tc.type,
                    function={"name": tc.function.name, "arguments": tc.function.arguments},
                )
                for tc in msg.tool_calls
            ]

        # reasoning_content (o1等推理模型)
        # OpenAI的o1模型会在message中返回reasoning_content字段
        if hasattr(msg, "reasoning_content") and msg.reasoning_content is not None:
            message.reasoning_content = msg.reasoning_content

        return message

    def _parse_usage(self, usage: Any) -> Usage:
        """解析token使用情况"""
        return Usage(
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            reasoning_tokens=getattr(usage, "reasoning_tokens", None),
        )

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
            except Exception as e:
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

    async def chat(self, request: LLMRequest) -> LLMResponse:
        """非流式对话"""
        try:
            params = self._build_request_params(request)
            params["stream"] = False

            # 带重试的请求
            response = await self._retry_with_backoff(
                self.client.chat.completions.create,
                **params,
            )

            choice = response.choices[0]
            message = self._parse_message(choice)
            usage = self._parse_usage(response.usage)

            return LLMResponse(
                message=message,
                usage=usage,
                finish_reason=choice.finish_reason,
                model=response.model,
            )

        except Exception as e:
            raise self._convert_error(e)

    async def stream_chat(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """流式对话"""
        try:
            params = self._build_request_params(request)
            params["stream"] = True
            params["stream_options"] = {"include_usage": True}

            # 带重试的请求
            stream = await self._retry_with_backoff(
                self.client.chat.completions.create,
                **params,
            )

            async for chunk in stream:
                if not chunk.choices:
                    # 最后一个chunk可能没有choices，只有usage
                    if hasattr(chunk, "usage") and chunk.usage:
                        yield StreamChunk(
                            delta=Message(role="assistant"),
                            usage=self._parse_usage(chunk.usage),
                            model=chunk.model,
                        )
                    continue

                choice = chunk.choices[0]
                delta = choice.delta

                # 构建delta message
                delta_msg = Message(role=delta.role if hasattr(delta, "role") else "assistant")

                if hasattr(delta, "content") and delta.content is not None:
                    delta_msg.content = delta.content

                if hasattr(delta, "tool_calls") and delta.tool_calls:
                    delta_msg.tool_calls = [
                        ToolCall(
                            id=tc.id if hasattr(tc, "id") else "",
                            type=tc.type if hasattr(tc, "type") else "function",
                            function=tc.function if hasattr(tc, "function") else {},
                        )
                        for tc in delta.tool_calls
                    ]

                if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                    delta_msg.reasoning_content = delta.reasoning_content

                # usage在最后的chunk中
                usage = None
                if hasattr(chunk, "usage") and chunk.usage:
                    usage = self._parse_usage(chunk.usage)

                yield StreamChunk(
                    delta=delta_msg,
                    finish_reason=choice.finish_reason,
                    usage=usage,
                    model=chunk.model,
                )

        except Exception as e:
            raise self._convert_error(e)
