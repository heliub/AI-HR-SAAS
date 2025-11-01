"""
LLM类型定义

遵循OpenAI标准格式，确保跨厂商兼容性
"""
from typing import Optional, List, Literal, Any, AsyncIterator
from pydantic import BaseModel, Field, field_validator


class ToolCall(BaseModel):
    """工具调用（OpenAI标准格式）"""
    id: str
    type: Literal["function"] = "function"
    function: dict  # {"name": str, "arguments": str(json)}


class Message(BaseModel):
    """消息（OpenAI标准格式）"""
    role: str  # "user" | "assistant" | "system" | "tool"
    content: Optional[str] = None

    # assistant调用工具时
    tool_calls: Optional[List[ToolCall]] = None

    # tool角色返回结果时
    tool_call_id: Optional[str] = None

    # 推理模型（如o1）的推理内容
    reasoning_content: Optional[str] = None


class Usage(BaseModel):
    """Token使用统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: Optional[int] = None  # 推理模型的额外token


class LLMRequest(BaseModel):
    """LLM请求"""
    model: str
    messages: List[Message]  # 对话消息（不包含system）

    # system prompt独立参数
    system: Optional[str] = None

    # 生成参数
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    stream: bool = False

    # 工具调用
    tools: Optional[List[dict]] = None
    tool_choice: Optional[Any] = None  # "auto" | "none" | {"type": "function", "function": {"name": "xxx"}}

    # 其他参数
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    stop: Optional[List[str]] = None

    @field_validator("messages")
    @classmethod
    def validate_no_system_in_messages(cls, messages: List[Message]) -> List[Message]:
        """确保messages中不包含system消息"""
        for msg in messages:
            if msg.role == "system":
                raise ValueError(
                    "messages中不应包含system消息，请使用system参数传递system prompt"
                )
        return messages


class LLMResponse(BaseModel):
    """LLM响应"""
    message: Message  # assistant的回复
    usage: Usage
    finish_reason: str  # "stop" | "length" | "tool_calls" | "content_filter"
    model: Optional[str] = None  # 实际使用的模型名

    @property
    def content(self) -> Optional[str]:
        """快捷获取文本内容"""
        return self.message.content

    @property
    def tool_calls(self) -> Optional[List[ToolCall]]:
        """快捷获取工具调用"""
        return self.message.tool_calls

    @property
    def reasoning_content(self) -> Optional[str]:
        """快捷获取推理内容"""
        return self.message.reasoning_content


class StreamChunk(BaseModel):
    """流式响应块"""
    delta: Message  # 增量内容
    finish_reason: Optional[str] = None
    usage: Optional[Usage] = None  # 最后一个chunk包含usage
    model: Optional[str] = None


class EmbeddingRequest(BaseModel):
    """Embedding请求"""
    model: str
    input: str | List[str]  # 单个文本或文本列表
    encoding_format: Optional[str] = None  # "float" | "base64"


class EmbeddingData(BaseModel):
    """单个Embedding数据"""
    embedding: List[float]
    index: int
    object: str = "embedding"


class EmbeddingUsage(BaseModel):
    """Embedding Token使用统计"""
    prompt_tokens: int
    total_tokens: int


class EmbeddingResponse(BaseModel):
    """Embedding响应"""
    data: List[EmbeddingData]
    model: str
    usage: EmbeddingUsage
    object: str = "list"
