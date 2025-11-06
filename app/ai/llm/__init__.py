"""
LLM模块

统一的LLM调用封装，支持多厂商（OpenAI、火山引擎等）

Examples:
    >>> from app.ai.llm import get_llm, LLMRequest, UserMessage

    >>> # 创建客户端
    >>> llm = get_llm(provider="openai")

    >>> # 非流式对话
    >>> request = LLMRequest(
    ...     model="gpt-4",
    ...     system="你是HR助手",
    ...     messages=[UserMessage(content="你好")]
    ... )
    >>> response = await llm.chat(request)
    >>> print(response.content)

    >>> # 流式对话
    >>> async for chunk in llm.stream_chat(request):
    ...     print(chunk.delta.content, end="")
"""
from .factory import get_llm, clear_cache, get_cache_info
from .types import (
    # 请求和响应
    LLMRequest,
    LLMResponse,
    StreamChunk,
    Usage,
    # 输入消息类型
    BaseMessage,
    SystemMessage,
    DeveloperMessage,
    UserMessage,
    AssistantMessage,
    ToolMessage,
    FunctionMessage,
    InputMessage,
    # 输出消息类型
    AssistantOutputMessage,
    # Content Part 类型
    TextContent,
    ImageUrl,
    ImageUrlContent,
    InputAudio,
    InputAudioContent,
    FileData,
    FileContent,
    RefusalContent,
    ContentPart,
    # Tool Call 类型
    FunctionCall,
    FunctionToolCall,
    CustomCall,
    CustomToolCall,
    ToolCall,
    # 音频输出
    AudioOutput,
)
from .errors import (
    LLMError,
    LLMAPIError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMValidationError,
)
from .base import BaseLLMClient

__all__ = [
    # 工厂函数
    "get_llm",
    "clear_cache",
    "get_cache_info",
    # 请求和响应
    "LLMRequest",
    "LLMResponse",
    "StreamChunk",
    "Usage",
    # 输入消息类型
    "BaseMessage",
    "SystemMessage",
    "DeveloperMessage",
    "UserMessage",
    "AssistantMessage",
    "ToolMessage",
    "FunctionMessage",
    "InputMessage",
    # 输出消息类型
    "AssistantOutputMessage",
    # Content Part 类型
    "TextContent",
    "ImageUrl",
    "ImageUrlContent",
    "InputAudio",
    "InputAudioContent",
    "FileData",
    "FileContent",
    "RefusalContent",
    "ContentPart",
    # Tool Call 类型
    "FunctionCall",
    "FunctionToolCall",
    "CustomCall",
    "CustomToolCall",
    "ToolCall",
    # 音频输出
    "AudioOutput",
    # 错误
    "LLMError",
    "LLMAPIError",
    "LLMTimeoutError",
    "LLMRateLimitError",
    "LLMAuthenticationError",
    "LLMValidationError",
    # 基类
    "BaseLLMClient",
]
