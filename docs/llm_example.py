"""
LLM封装使用示例

演示基本用法和常见场景
"""
import asyncio
from app.ai import get_llm, LLMRequest, UserMessage, SystemMessage, AssistantMessage


async def example_basic_chat():
    """基础对话示例"""
    print("=== 基础对话示例 ===")

    # 创建客户端（从配置读取）
    llm = get_llm(provider="volcengine")

    # 构建请求
    request = LLMRequest(
        model="ep-20241028112534-4sjqw",  # 根据实际模型调整
        system="你是专业的HR助手，帮助分析简历和职位匹配度。",
        messages=[
            UserMessage(content="你好，介绍一下你自己")
        ],
        temperature=0.7,
        max_completion_tokens=500
    )

    # 调用
    response = await llm.chat(request)
    print(f"回复: {response.content}")
    print(f"Token使用: {response.usage.total_tokens}")
    print(f"完成原因: {response.finish_reason}")
    print()


async def example_stream_chat():
    """流式对话示例"""
    print("=== 流式对话示例 ===")

    llm = get_llm(provider="volcengine")

    request = LLMRequest(
        model="ep-20241028112534-4sjqw",
        system="你是专业的HR助手",
        messages=[
            UserMessage(content="请简要介绍Python工程师需要的核心技能")
        ],
        stream=True,
        temperature=0.7
    )

    print("流式输出: ", end="", flush=True)
    async for chunk in llm.stream_chat(request):
        if chunk.delta.content:
            print(chunk.delta.content, end="", flush=True)

        if chunk.usage:
            print(f"\n\nToken使用: {chunk.usage.total_tokens}")

    print()


async def example_multi_turn():
    """多轮对话示例"""
    print("=== 多轮对话示例 ===")

    llm = get_llm(provider="volcengine")
    messages = []

    # 第一轮
    messages.append(UserMessage(content="我需要招聘一个Python后端工程师"))
    response = await llm.chat(LLMRequest(
        model="ep-20241028112534-4sjqw",
        system="你是HR助手",
        messages=messages
    ))
    print(f"用户: {messages[-1].content}")
    print(f"助手: {response.content}\n")
    messages.append(response.message)

    # 第二轮
    messages.append(UserMessage(content="需要几年工作经验？"))
    response = await llm.chat(LLMRequest(
        model="ep-20241028112534-4sjqw",
        system="你是HR助手",
        messages=messages
    ))
    print(f"用户: {messages[-1].content}")
    print(f"助手: {response.content}\n")
    print()


async def example_error_handling():
    """错误处理示例"""
    print("=== 错误处理示例 ===")

    from app.ai import (
        LLMError,
        LLMAPIError,
        LLMTimeoutError,
        LLMRateLimitError,
        LLMAuthenticationError,
        LLMValidationError
    )

    try:
        # 测试：messages中包含system会报错
        llm = get_llm(provider="volcengine")
        request = LLMRequest(
            model="ep-20241028112534-4sjqw",
            messages=[
                SystemMessage(content="错误的用法"),  # 这会报错
                UserMessage(content="你好")
            ]
        )
        await llm.chat(request)
    except LLMValidationError as e:
        print(f"✓ 捕获到预期的验证错误: {e.message}")

    try:
        # 测试：不支持的provider
        llm = get_llm(provider="unknown_provider")
    except LLMValidationError as e:
        print(f"✓ 捕获到预期的验证错误: {e.message}")

    print()


async def example_explicit_params():
    """显式传参示例"""
    print("=== 显式传参示例 ===")

    # 不使用配置，直接传API密钥
    llm = get_llm(
        provider="volcengine",
        api_key="your_api_key_here",
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        timeout=30.0,
        max_retries=2
    )

    print("✓ 客户端创建成功（显式传参）")
    print(f"  Provider: {llm.provider_name}")
    print(f"  Timeout: {llm.timeout}s")
    print(f"  Max Retries: {llm.max_retries}")
    print()


async def main():
    """运行所有示例"""
    print("LLM封装使用示例\n")

    # 错误处理（不需要真实API调用）
    await example_error_handling()

    # 显式传参（不需要真实API调用）
    await example_explicit_params()

    # 以下示例需要真实的API密钥和网络连接
    # 取消注释运行：

    # await example_basic_chat()
    # await example_stream_chat()
    # await example_multi_turn()

    print("所有示例运行完成！")


if __name__ == "__main__":
    asyncio.run(main())
