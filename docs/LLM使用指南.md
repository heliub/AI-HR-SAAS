# LLM调用封装使用指南

## 快速开始

### 1. 基础配置

在 `.env` 文件中配置API密钥：

```bash
# OpenAI
OPENAI_API_KEY=sk-xxx

# 火山引擎
VOLCENGINE_API_KEY=your_volcengine_key
```

在 `app/core/config.py` 的 `AI_PROVIDERS` 中配置provider：

```python
AI_PROVIDERS: List[Dict] = [
    {
        "provider": "openai",
        "base_url": "https://api.openai.com/v1",
        "api_key": ""  # 会自动从环境变量读取
    },
    {
        "provider": "volcengine",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key": ""  # 会自动从环境变量读取
    }
]
```

### 2. 基础用法

#### 非流式对话

```python
from app.ai import get_llm, LLMRequest, UserMessage, SystemMessage, AssistantMessage, ToolMessage

# 创建客户端（从配置读取）
llm = get_llm(provider="openai")

# 构建请求
request = LLMRequest(
    model="gpt-4",
    system="你是专业的HR助手",
    messages=[
        UserMessage(content="请帮我分析这份简历")
    ],
    temperature=0.7
)

# 调用
response = await llm.chat(request)
print(response.content)  # 模型回复的文本
print(response.usage.total_tokens)  # token使用量
```

#### 流式对话

```python
request = LLMRequest(
    model="gpt-4",
    system="你是专业的HR助手",
    messages=[UserMessage(content="介绍一下你自己")],
    stream=True
)

async for chunk in llm.stream_chat(request):
    if chunk.delta.content:
        print(chunk.delta.content, end="", flush=True)

    # 最后一个chunk包含usage
    if chunk.usage:
        print(f"\n总token: {chunk.usage.total_tokens}")
```

### 3. 多轮对话

```python
messages = []

# 第一轮
messages.append(UserMessage(content="我需要招聘一个Python工程师"))
response = await llm.chat(LLMRequest(
    model="gpt-4",
    system="你是HR助手",
    messages=messages
))
messages.append(response.message)  # 添加assistant的回复

# 第二轮
messages.append(UserMessage(content="需要哪些技能要求？"))
response = await llm.chat(LLMRequest(
    model="gpt-4",
    system="你是HR助手",
    messages=messages
))
```

### 4. Tool调用

```python
# 定义tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_resume",
            "description": "获取简历详情",
            "parameters": {
                "type": "object",
                "properties": {
                    "resume_id": {
                        "type": "integer",
                        "description": "简历ID"
                    }
                },
                "required": ["resume_id"]
            }
        }
    }
]

request = LLMRequest(
    model="gpt-4",
    system="你是HR助手，可以调用工具查询简历",
    messages=[UserMessage(content="查看ID为123的简历")],
    tools=tools
)

response = await llm.chat(request)

# 检查是否要调用工具
if response.finish_reason == "tool_calls":
    for tool_call in response.tool_calls:
        print(f"调用工具: {tool_call.function['name']}")
        print(f"参数: {tool_call.function['arguments']}")

        # 执行工具
        import json
        args = json.loads(tool_call.function['arguments'])
        result = get_resume(args['resume_id'])  # 你的业务逻辑

        # 继续对话
        request.messages.append(response.message)  # assistant的tool_calls
        request.messages.append(ToolMessage(
            tool_call_id=tool_call.id,
            content=str(result)
        ))

        # 获取最终回复
        final_response = await llm.chat(request)
        print(final_response.content)
```

### 5. 推理模型（o1）

```python
request = LLMRequest(
    model="o1-preview",
    messages=[UserMessage(content="复杂的数学问题...")]
)

response = await llm.chat(request)

# o1模型会返回推理内容
if response.reasoning_content:
    print("思考过程:")
    print(response.reasoning_content)
    print("\n最终答案:")
    print(response.content)
```

### 6. 显式传参（不使用配置）

```python
# 直接传API密钥和base_url
llm = get_llm(
    provider="openai",
    api_key="sk-xxx",
    base_url="https://api.openai.com/v1",
    timeout=30.0,
    max_retries=3
)
```

### 7. 错误处理

```python
from app.ai import (
    LLMError,
    LLMAPIError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError
)

try:
    response = await llm.chat(request)
except LLMAuthenticationError as e:
    print(f"认证失败: {e}")
except LLMRateLimitError as e:
    print(f"限流: {e}, 重试等待: {e.retry_after}秒")
except LLMTimeoutError as e:
    print(f"超时: {e}")
except LLMAPIError as e:
    print(f"API错误: {e.status_code} - {e.message}")
except LLMError as e:
    print(f"其他错误: {e}")
```

## 支持的Provider

- `openai` - OpenAI官方API
- `volcengine` - 火山引擎（兼容OpenAI格式）

## 重要约定

1. **system prompt独立传递**
   - 使用 `system` 参数，不要在 `messages` 中包含system消息
   - 否则会抛出 `ValidationError`

2. **消息格式**
   - 遵循OpenAI标准格式
   - 业务层不需要关心不同厂商的差异

3. **自动重试**
   - 超时、限流、5xx错误会自动重试3次
   - 指数退避: 1s, 2s, 4s
   - 4xx错误（如参数错误）不会重试

4. **Token统计**
   - 每次响应都包含 `usage` 字段
   - 推理模型会额外返回 `reasoning_tokens`

## 最佳实践

1. **复用客户端实例**
   ```python
   # 应用启动时创建
   llm_client = get_llm(provider="openai")

   # 在不同请求中复用
   response1 = await llm_client.chat(request1)
   response2 = await llm_client.chat(request2)
   ```

2. **合理设置超时**
   ```python
   # 简单任务：短超时
   llm = get_llm(provider="openai", timeout=30.0)

   # 复杂任务：长超时
   llm = get_llm(provider="openai", timeout=120.0)
   ```

3. **使用流式响应提升用户体验**
   ```python
   # 对于长回复，使用流式
   async for chunk in llm.stream_chat(request):
       await websocket.send_text(chunk.delta.content or "")
   ```

4. **妥善处理错误**
   - 限流：等待后重试
   - 超时：降低任务复杂度或增加超时时间
   - 认证失败：检查API密钥

## 扩展新的Provider

```python
# app/ai/llm/providers/my_provider.py
from ..base import BaseLLMClient
from ..types import LLMRequest, LLMResponse

class MyProviderClient(BaseLLMClient):
    @property
    def provider_name(self) -> str:
        return "my_provider"

    async def chat(self, request: LLMRequest) -> LLMResponse:
        # 实现你的逻辑
        pass

    async def stream_chat(self, request: LLMRequest):
        # 实现流式逻辑
        pass

# app/ai/llm/factory.py
from .providers import MyProviderClient

PROVIDER_REGISTRY = {
    "openai": OpenAIClient,
    "volcengine": VolcengineClient,
    "my_provider": MyProviderClient,  # 注册新provider
}
```
