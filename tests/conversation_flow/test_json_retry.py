"""
测试JSON解析失败的重试机制

验证JSON解析失败时会触发重试，而不是直接崩溃
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.ai.llm.errors import LLMError
from app.conversation_flow.nodes.precheck import N1TransferHumanIntentNode
from app.conversation_flow.models import NodeAction


class TestJSONParseRetry:
    """测试JSON解析重试机制"""

    @pytest.mark.asyncio
    async def test_json_parse_error_triggers_retry(self, sample_context, mock_llm_caller):
        """JSON解析失败应该触发重试，不是直接抛出JSONDecodeError"""
        node = N1TransferHumanIntentNode()

        # Mock: 前2次返回无效JSON，第3次返回有效JSON
        mock_llm_caller.call_with_scene.side_effect = [
            {"content": "这不是JSON"},  # 第1次：无效JSON
            {"content": "{incomplete"},  # 第2次：不完整JSON
            {"transfer": "no"}           # 第3次：有效JSON
        ]

        # 执行节点
        result = await node.execute(sample_context)

        # 验证：重试了3次
        assert mock_llm_caller.call_with_scene.call_count == 3, "应该重试了3次"

        # 验证：最终成功返回
        assert result.action == NodeAction.CONTINUE
        assert result.data["transfer_intent"] is False

    @pytest.mark.asyncio
    async def test_json_parse_error_max_retries_then_fallback(self, sample_context, mock_llm_caller):
        """JSON解析失败3次后，应该触发降级"""
        node = N1TransferHumanIntentNode()

        # Mock: 3次都返回无效JSON
        mock_llm_caller.call_with_scene.side_effect = [
            {"content": "invalid json 1"},
            {"content": "invalid json 2"},
            {"content": "invalid json 3"}
        ]

        # 执行节点
        result = await node.execute(sample_context)

        # 验证：重试了3次
        assert mock_llm_caller.call_with_scene.call_count == 3

        # 验证：触发降级，返回CONTINUE（N1的降级策略）
        assert result.action == NodeAction.CONTINUE
        assert result.data["fallback"] is True
        assert result.data["transfer_intent"] is False

    @pytest.mark.asyncio
    async def test_json_parse_error_is_wrapped_as_llm_error(self, sample_context):
        """验证JSONDecodeError被包装成LLMError"""
        from app.ai import LLMCaller

        llm_caller = LLMCaller()

        # 直接测试_parse_json_response方法
        with pytest.raises(LLMError) as exc_info:
            llm_caller._parse_json_response("这不是有效的JSON", scene_name="test")

        # 验证异常类型
        assert "JSON解析失败" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self, sample_context, mock_llm_caller):
        """验证重试时使用指数退避"""
        node = N1TransferHumanIntentNode()

        # Mock: 前2次失败，第3次成功
        mock_llm_caller.call_with_scene.side_effect = [
            {"content": "invalid 1"},
            {"content": "invalid 2"},
            {"transfer": "no"}
        ]

        # 使用patch监控asyncio.sleep
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            result = await node.execute(sample_context)

            # 验证：调用了2次sleep（第1次重试等1秒，第2次重试等2秒）
            assert mock_sleep.call_count == 2
            # 验证指数退避：第1次1秒(2^0)，第2次2秒(2^1)
            assert mock_sleep.call_args_list[0][0][0] == 1  # 2^0
            assert mock_sleep.call_args_list[1][0][0] == 2  # 2^1

    @pytest.mark.asyncio
    async def test_valid_json_no_retry(self, sample_context, mock_llm_caller):
        """第一次就返回有效JSON，不应该重试"""
        node = N1TransferHumanIntentNode()

        # Mock: 第一次就返回有效JSON
        mock_llm_caller.call_with_scene.return_value = {"transfer": "no"}

        result = await node.execute(sample_context)

        # 验证：只调用了1次
        assert mock_llm_caller.call_with_scene.call_count == 1
        assert result.action == NodeAction.CONTINUE

    @pytest.mark.asyncio
    async def test_json_with_markdown_code_block(self, sample_context, mock_llm_caller):
        """LLM返回带markdown代码块的JSON，应该能正确解析"""
        node = N1TransferHumanIntentNode()

        # Mock: 返回带```json```的响应
        mock_llm_caller.call_with_scene.return_value = {
            "content": '```json\n{"transfer": "no"}\n```'
        }

        # 直接测试LLMCaller的解析
        from app.ai import LLMCaller
        llm_caller = LLMCaller()
        result = llm_caller._parse_json_response(
            '```json\n{"transfer": "no"}\n```',
            scene_name="test"
        )

        assert result == {"transfer": "no"}

    @pytest.mark.asyncio
    async def test_json_with_simple_code_block(self, sample_context):
        """LLM返回带```的响应（不带json标记），也应该能解析"""
        from app.ai import LLMCaller
        llm_caller = LLMCaller()

        result = llm_caller._parse_json_response(
            '```\n{"transfer": "yes"}\n```',
            scene_name="test"
        )

        assert result == {"transfer": "yes"}


class TestOtherLLMErrors:
    """测试其他LLM错误也会重试"""

    @pytest.mark.asyncio
    async def test_llm_connection_error_retries(self, sample_context, mock_llm_caller):
        """LLM连接失败应该重试"""
        node = N1TransferHumanIntentNode()

        # Mock: 前2次连接失败，第3次成功
        mock_llm_caller.call_with_scene.side_effect = [
            LLMError("连接超时"),
            LLMError("连接超时"),
            {"transfer": "no"}
        ]

        result = await node.execute(sample_context)

        # 验证：重试了3次
        assert mock_llm_caller.call_with_scene.call_count == 3
        assert result.action == NodeAction.CONTINUE

    @pytest.mark.asyncio
    async def test_llm_timeout_error_retries(self, sample_context, mock_llm_caller):
        """LLM超时应该重试"""
        node = N1TransferHumanIntentNode()

        # Mock: 前2次超时，第3次成功
        mock_llm_caller.call_with_scene.side_effect = [
            LLMError("请求超时"),
            LLMError("请求超时"),
            {"transfer": "no"}
        ]

        result = await node.execute(sample_context)

        assert mock_llm_caller.call_with_scene.call_count == 3

    @pytest.mark.asyncio
    async def test_non_llm_error_no_retry(self, sample_context, mock_llm_caller):
        """非LLM错误不应该重试，直接抛出"""
        node = N1TransferHumanIntentNode()

        # Mock: 抛出非LLM错误
        mock_llm_caller.call_with_scene.side_effect = ValueError("参数错误")

        # 验证：直接抛出，不重试
        with pytest.raises(ValueError, match="参数错误"):
            await node.execute(sample_context)

        # 验证：只调用了1次
        assert mock_llm_caller.call_with_scene.call_count == 1
