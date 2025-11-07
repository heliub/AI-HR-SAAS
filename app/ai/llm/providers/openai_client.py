"""
OpenAI Provider

支持OpenAI官方API和兼容OpenAI格式的其他厂商
"""
import asyncio
from typing import AsyncIterator, Any, Dict, List
from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError, AuthenticationError

from ..base import BaseLLMClient
from ..types import (
    LLMRequest,
    LLMResponse,
    StreamChunk,
    Usage,
    # 输入消息类型
    InputMessage,
    SystemMessage,
    AssistantMessage,
    # 输出消息类型
    AssistantOutputMessage,
    # Tool Call 类型
    FunctionCall,
    FunctionToolCall,
    CustomCall,
    CustomToolCall,
    # 音频输出
    AudioOutput,
)
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
        构建消息列表，自动处理 system prompt

        Args:
            request: LLM请求

        Returns:
            消息列表
        """
        messages = []

        # 如果有 system 参数，插入到最前面
        if request.system:
            messages.append({"role": "system", "content": request.system})

        # 添加对话消息
        for msg in request.messages:
            # 先获取基础字段
            msg_dict = msg.model_dump(exclude_none=True)

            # 特殊处理 content 数组（如果包含对象，需要序列化）
            if hasattr(msg, "content") and isinstance(msg.content, list):
                msg_dict["content"] = [
                    part if isinstance(part, str) else part.model_dump(exclude_none=True)
                    for part in msg.content
                ]

            # 特殊处理 tool_calls（确保序列化）
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                msg_dict["tool_calls"] = [
                    tc.model_dump(exclude_none=True) for tc in msg.tool_calls
                ]

            # 特殊处理 audio（确保格式正确）
            if hasattr(msg, "audio") and msg.audio:
                msg_dict["audio"] = msg.audio.model_dump(exclude_none=True)

            messages.append(msg_dict)

        return messages

    def _build_request_params(self, request: LLMRequest) -> Dict[str, Any]:
        """构建请求参数"""
        params = {
            "model": request.model,
            "messages": self._build_messages(request),
            "stream": request.stream,
        }
        
        # GPT-5模型不支持自定义温度参数，只支持默认值1
        # 因此对于GPT-5模型，不传递temperature参数
        if not request.model.startswith("gpt-5"):
            params["temperature"] = request.temperature

        # 可选参数
        if request.max_completion_tokens is not None:
            params["max_completion_tokens"] = request.max_completion_tokens
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
        
        # # 推理模型参数（如 o1 系列）
        # if request.reasoning_effort is not None:
        #     params["reasoning_effort"] = request.reasoning_effort
        
        # 动态参数，支持不同模型的差异化参数
        if request.additional_params is not None:
            params.update(request.additional_params)

        return params

    def _parse_message(self, choice: Any) -> AssistantOutputMessage:
        """解析响应消息"""
        msg = choice.message
        message = AssistantOutputMessage(role="assistant")

        # content
        if hasattr(msg, "content") and msg.content is not None:
            message.content = msg.content

        # refusal
        if hasattr(msg, "refusal") and msg.refusal is not None:
            message.refusal = msg.refusal

        # audio (完整的音频数据)
        if hasattr(msg, "audio") and msg.audio is not None:
            message.audio = AudioOutput(
                data=msg.audio.data,
                expires_at=msg.audio.expires_at,
                id=msg.audio.id,
                transcript=msg.audio.transcript,
            )

        # tool_calls
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            parsed_calls = []
            for tc in msg.tool_calls:
                if tc.type == "function":
                    parsed_calls.append(
                        FunctionToolCall(
                            id=tc.id,
                            type="function",
                            function=FunctionCall(
                                name=tc.function.name,
                                arguments=tc.function.arguments,
                            ),
                        )
                    )
                elif tc.type == "custom":
                    parsed_calls.append(
                        CustomToolCall(
                            id=tc.id,
                            type="custom",
                            custom=CustomCall(
                                name=tc.custom.name,
                                input=tc.custom.input,
                            ),
                        )
                    )
            message.tool_calls = parsed_calls

        # reasoning_content (o1等推理模型)
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
                            delta=AssistantOutputMessage(role="assistant"),
                            usage=self._parse_usage(chunk.usage),
                            model=chunk.model,
                        )
                    continue

                choice = chunk.choices[0]
                delta = choice.delta

                # 构建 delta message
                delta_msg = AssistantOutputMessage(role="assistant")

                if hasattr(delta, "content") and delta.content is not None:
                    delta_msg.content = delta.content

                if hasattr(delta, "refusal") and delta.refusal is not None:
                    delta_msg.refusal = delta.refusal

                if hasattr(delta, "audio") and delta.audio is not None:
                    # 流式响应中的 audio 可能是增量数据
                    delta_msg.audio = AudioOutput(
                        data=delta.audio.data if hasattr(delta.audio, "data") else "",
                        expires_at=delta.audio.expires_at if hasattr(delta.audio, "expires_at") else 0,
                        id=delta.audio.id if hasattr(delta.audio, "id") else "",
                        transcript=delta.audio.transcript if hasattr(delta.audio, "transcript") else "",
                    )

                if hasattr(delta, "tool_calls") and delta.tool_calls:
                    parsed_delta_calls = []
                    for tc in delta.tool_calls:
                        tc_type = tc.type if hasattr(tc, "type") else "function"
                        if tc_type == "function":
                            func_call = FunctionCall(
                                name=tc.function.name if hasattr(tc.function, "name") else "",
                                arguments=tc.function.arguments if hasattr(tc.function, "arguments") else "",
                            )
                            parsed_delta_calls.append(
                                FunctionToolCall(
                                    id=tc.id if hasattr(tc, "id") else "",
                                    type="function",
                                    function=func_call,
                                )
                            )
                    delta_msg.tool_calls = parsed_delta_calls if parsed_delta_calls else None

                if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                    delta_msg.reasoning_content = delta.reasoning_content

                # usage 在最后的 chunk 中
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
