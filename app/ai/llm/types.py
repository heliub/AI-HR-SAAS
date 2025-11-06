"""
LLM类型定义

遵循OpenAI标准格式，确保跨厂商兼容性
"""
from typing import Optional, List, Literal, Any, AsyncIterator, Union, Dict
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Content Part 类型定义（用于 content 数组）
# ============================================================================

class TextContent(BaseModel):
    """文本内容对象"""
    type: Literal["text"] = "text"
    text: str


class ImageUrl(BaseModel):
    """图片URL配置"""
    url: str  # URL 或 base64 编码的图片数据
    detail: Optional[Literal["auto", "low", "high"]] = "auto"


class ImageUrlContent(BaseModel):
    """图片URL内容对象（仅支持 user 角色）"""
    type: Literal["image_url"] = "image_url"
    image_url: ImageUrl


class InputAudio(BaseModel):
    """音频输入配置"""
    data: str  # base64 编码的音频数据
    format: Literal["wav", "mp3"]  # 音频格式


class InputAudioContent(BaseModel):
    """音频输入内容对象（仅支持 user 角色）"""
    type: Literal["input_audio"] = "input_audio"
    input_audio: InputAudio


class FileData(BaseModel):
    """文件数据配置"""
    file_data: Optional[str] = None  # base64 编码的文件数据
    file_id: Optional[str] = None    # 上传文件的 ID
    filename: Optional[str] = None   # 文件名


class FileContent(BaseModel):
    """文件内容对象（仅支持 user 角色）"""
    type: Literal["file"] = "file"
    file: FileData


class RefusalContent(BaseModel):
    """拒绝内容对象（仅支持 assistant 角色）"""
    type: Literal["refusal"] = "refusal"
    refusal: str  # 拒绝消息


# Content Part 联合类型
# 注意：content 数组还可以包含纯字符串元素
ContentPart = Union[str, TextContent, ImageUrlContent, InputAudioContent, FileContent, RefusalContent]


# ============================================================================
# Tool Call 类型定义
# ============================================================================

class FunctionCall(BaseModel):
    """函数调用详情"""
    name: str  # 函数名
    arguments: str  # JSON 格式的参数字符串


class FunctionToolCall(BaseModel):
    """函数工具调用"""
    id: str  # 工具调用 ID
    type: Literal["function"] = "function"
    function: FunctionCall  # 结构化对象


class CustomCall(BaseModel):
    """自定义工具调用详情"""
    name: str  # 工具名称
    input: Any  # 输入参数（任意类型）


class CustomToolCall(BaseModel):
    """自定义工具调用"""
    id: str  # 工具调用 ID
    type: Literal["custom"] = "custom"
    custom: CustomCall  # 结构化对象


# Tool Call 联合类型
ToolCall = Union[FunctionToolCall, CustomToolCall]


# ============================================================================
# 音频响应类型
# ============================================================================

class AudioOutput(BaseModel):
    """音频输出（大模型响应中的音频数据）"""
    data: str  # Base64 编码的音频字节
    expires_at: int  # Unix 时间戳，音频过期时间
    id: str  # 音频响应的唯一 ID
    transcript: str  # 音频的转录文本


# ============================================================================
# 输入消息类型（用于请求）
# ============================================================================

class BaseMessage(BaseModel):
    """消息基类"""
    role: str


class SystemMessage(BaseMessage):
    """系统消息"""
    role: Literal["system"] = "system"
    content: str  # system 只支持字符串


class DeveloperMessage(BaseMessage):
    """开发者消息"""
    role: Literal["developer"] = "developer"
    content: Union[str, List[ContentPart]]
    name: Optional[str] = None


class UserMessage(BaseMessage):
    """用户消息（支持多模态）"""
    role: Literal["user"] = "user"
    content: Union[str, List[ContentPart]]  # 支持文本、图片、音频、文件
    name: Optional[str] = None


class AssistantMessage(BaseMessage):
    """Assistant 消息（用于多轮对话历史）"""
    role: Literal["assistant"] = "assistant"
    content: Optional[str] = None
    name: Optional[str] = None
    refusal: Optional[str] = None
    audio: Optional[AudioOutput] = None  # 历史消息中可能包含音频
    tool_calls: Optional[List[ToolCall]] = None


class ToolMessage(BaseMessage):
    """工具返回消息"""
    role: Literal["tool"] = "tool"
    content: str  # tool 只支持字符串
    tool_call_id: str  # 必需，对应的工具调用 ID


class FunctionMessage(BaseModel):
    """函数消息（legacy）"""
    role: Literal["function"] = "function"
    content: str  # function 只支持字符串
    name: str  # 必需


# 输入消息联合类型
InputMessage = Union[
    SystemMessage,
    DeveloperMessage,
    UserMessage,
    AssistantMessage,
    ToolMessage,
    FunctionMessage,
]


# ============================================================================
# 输出消息类型（用于响应）
# ============================================================================

class AssistantOutputMessage(BaseModel):
    """大模型返回的 Assistant 消息"""
    role: Literal["assistant"] = "assistant"
    content: Optional[str] = None
    refusal: Optional[str] = None
    audio: Optional[AudioOutput] = None
    tool_calls: Optional[List[ToolCall]] = None
    # 注意：输出消息没有 name 字段

    # 推理模型（如 o1）的推理内容
    reasoning_content: Optional[str] = None


class Usage(BaseModel):
    """Token使用统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: Optional[int] = None  # 推理模型的额外token


class LLMRequest(BaseModel):
    """
    LLM请求
    
    支持OpenAI标准格式，确保跨厂商兼容性。
    包含基础参数、推理模型参数和动态参数支持。
    
    Attributes:
        model: 模型名称，如 "gpt-4", "gpt-3.5-turbo", "o1-preview" 等
        messages: 对话消息列表，包含用户、助手、系统等角色的消息
        system: 系统提示词（可选，也可以在 messages 中使用 SystemMessage）
        temperature: 控制输出的随机性，范围 0.0-2.0，默认 0.7
        max_completion_tokens: 最大完成令牌数（可选）
        stream: 是否使用流式响应，默认 False
        reasoning_effort: 推理模型（如 o1 系列）的推理努力程度，可选值：
            - "minimal": 最小努力，响应更快但推理较浅
            - "low": 低努力
            - "medium": 中等努力（推荐）
            - "high": 高努力，推理更深但响应较慢
        tools: 工具定义列表（可选）
        tool_choice: 工具选择策略（可选）
        top_p: 核采样参数，范围 0.0-1.0（可选）
        frequency_penalty: 频率惩罚，范围 -2.0-2.0（可选）
        presence_penalty: 存在惩罚，范围 -2.0-2.0（可选）
        stop: 停止词列表（可选）
        additional_params: 动态参数字典，支持不同模型的差异化参数
            例如：{"response_format": {"type": "json_object"}}
    
    Examples:
        >>> # 基础请求
        >>> request = LLMRequest(
        ...     model="gpt-4",
        ...     messages=[UserMessage(content="你好")],
        ... )
        
        >>> # 带推理努力的请求
        >>> request = LLMRequest(
        ...     model="o1-preview",
        ...     messages=[UserMessage(content="解释量子计算")],
        ...     reasoning_effort="high"
        ... )
        
        >>> # 带动态参数的请求
        >>> request = LLMRequest(
        ...     model="gpt-4",
        ...     messages=[UserMessage(content="生成JSON")],
        ...     additional_params={"response_format": {"type": "json_object"}}
        ... )
    """
    model: str
    messages: List[InputMessage]  # 对话消息

    # system prompt独立参数（可选，也可以在 messages 中使用 SystemMessage）
    system: Optional[str] = None

    # 生成参数
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_completion_tokens: Optional[int] = Field(default=None, ge=1)
    stream: bool = False

    # 推理模型参数（如 o1 系列）
    reasoning_effort: Optional[Literal["minimal", "low", "medium", "high"]] = None

    # 工具调用
    tools: Optional[List[dict]] = None
    tool_choice: Optional[Any] = None  # "auto" | "none" | {"type": "function", "function": {"name": "xxx"}}

    # 其他参数
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    stop: Optional[List[str]] = None
    
    # 动态参数，支持不同模型的差异化参数
    additional_params: Optional[Dict[str, Any]] = None

    @field_validator("messages")
    @classmethod
    def validate_messages(cls, messages: List[InputMessage]) -> List[InputMessage]:
        """验证消息列表"""
        if not messages:
            raise ValueError("messages 不能为空")
        return messages


class LLMResponse(BaseModel):
    """LLM响应"""
    message: AssistantOutputMessage  # assistant 的回复
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

    @property
    def refusal(self) -> Optional[str]:
        """快捷获取拒绝消息"""
        return self.message.refusal

    @property
    def audio(self) -> Optional[AudioOutput]:
        """快捷获取音频响应"""
        return self.message.audio


class StreamChunk(BaseModel):
    """流式响应块"""
    delta: AssistantOutputMessage  # 增量内容
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
