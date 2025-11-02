"""
测试各节点的降级策略

验证关键节点在LLM失败时的降级行为是否符合预期
"""
import pytest
from app.ai.llm.errors import LLMError
from app.conversation_flow.models import NodeAction
from app.conversation_flow.nodes.precheck import (
    N1TransferHumanIntentNode,
    N2EmotionAnalysisNode
)
from app.conversation_flow.nodes.response import (
    N3ContinueConversationNode,
    N4AskQuestionNode,
    N10FallbackAnswerNode
)


class TestN1Fallback:
    """测试N1降级策略：假定不转人工"""

    def test_fallback_returns_continue(self, sample_context):
        """降级时应返回CONTINUE而不是SUSPEND"""
        node = N1TransferHumanIntentNode()
        result = node._fallback_result(sample_context, LLMError("LLM故障"))

        assert result.node_name == "N1"
        assert result.action == NodeAction.CONTINUE, "N1降级应该继续流程，不应该转人工"
        assert result.data["transfer_intent"] is False
        assert result.data["fallback"] is True

    def test_fallback_records_exception(self, sample_context):
        """降级时应记录异常信息"""
        exception = LLMError("连接超时")
        node = N1TransferHumanIntentNode()
        result = node._fallback_result(sample_context, exception)

        assert result.data["fallback_reason"] == "连接超时"


class TestN2Fallback:
    """测试N2降级策略：假定情感正常"""

    def test_fallback_returns_normal_emotion(self, sample_context):
        """降级时应返回正常情感(分数1)"""
        node = N2EmotionAnalysisNode()
        result = node._fallback_result(sample_context, LLMError("LLM故障"))

        assert result.node_name == "N2"
        assert result.action == NodeAction.CONTINUE
        assert result.data["emotion_score"] == 1, "N2降级应假定情感正常(分数1)"
        assert result.data["need_closing"] is False
        assert result.data["fallback"] is True

    def test_fallback_reason_message(self, sample_context):
        """降级原因应该友好"""
        node = N2EmotionAnalysisNode()
        result = node._fallback_result(sample_context, LLMError("JSON解析失败"))

        assert "技术故障" in result.data["emotion_reason"]
        assert "假定情感正常" in result.data["emotion_reason"]


class TestN3Fallback:
    """测试N3降级策略：假定愿意沟通"""

    def test_fallback_returns_willing(self, sample_context):
        """降级时应返回愿意沟通"""
        node = N3ContinueConversationNode()
        result = node._fallback_result(sample_context, LLMError("LLM故障"))

        assert result.node_name == "N3"
        assert result.action == NodeAction.CONTINUE
        assert result.data["willing"] is True, "N3降级应假定候选人愿意沟通"
        assert result.data["fallback"] is True


class TestN4Fallback:
    """测试N4降级策略：假定未发问，走闲聊"""

    def test_fallback_returns_not_question(self, sample_context):
        """降级时应返回未发问"""
        node = N4AskQuestionNode()
        result = node._fallback_result(sample_context, LLMError("LLM故障"))

        assert result.node_name == "N4"
        assert result.action == NodeAction.CONTINUE
        assert result.data["is_question"] is False, "N4降级应假定未发问，走闲聊路径（最安全）"
        assert result.data["question_type"] == ""


class TestN10Fallback:
    """测试N10降级策略：返回固定友好消息"""

    def test_fallback_returns_friendly_message(self, sample_context):
        """降级时应返回固定的友好消息"""
        node = N10FallbackAnswerNode()
        result = node._fallback_result(sample_context, LLMError("LLM故障"))

        assert result.node_name == "N10"
        assert result.action == NodeAction.SEND_MESSAGE
        assert "感谢" in result.message, "N10降级消息应该友好"
        assert "咨询" in result.message
        assert result.data["technical_fallback"] is True

    def test_fallback_message_is_user_friendly(self, sample_context):
        """降级消息应该对用户友好，不泄露技术细节"""
        node = N10FallbackAnswerNode()
        result = node._fallback_result(sample_context, LLMError("ConnectionError: 127.0.0.1:8080"))

        # 消息不应包含技术细节
        assert "ConnectionError" not in result.message
        assert "127.0.0.1" not in result.message
        # 技术细节应该在data里
        assert "ConnectionError" in result.data["fallback_reason"]


class TestDefaultFallback:
    """测试基类的默认降级策略"""

    def test_default_fallback_suspends(self, sample_context, mock_db):
        """没有覆盖降级方法的节点，默认应该转人工"""
        from app.conversation_flow.nodes.base import NodeExecutor

        class CustomNode(NodeExecutor):
            async def _do_execute(self, context):
                raise NotImplementedError()

        node = CustomNode(node_name="TestNode", scene_name="test", db=mock_db)
        result = node._fallback_result(sample_context, LLMError("测试"))

        assert result.action == NodeAction.SUSPEND
        assert "系统繁忙" in result.reason, "默认降级消息应该对用户友好"
        assert result.data["fallback"] is True

    def test_default_fallback_separates_user_and_tech_info(self, sample_context, mock_db):
        """默认降级应该区分用户消息和技术日志"""
        from app.conversation_flow.nodes.base import NodeExecutor

        class CustomNode(NodeExecutor):
            async def _do_execute(self, context):
                raise NotImplementedError()

        node = CustomNode(node_name="TestNode", scene_name="test", db=mock_db)
        exception = LLMError("Internal Server Error: database connection failed")
        result = node._fallback_result(sample_context, exception)

        # reason是给用户看的，应该友好
        assert "Internal Server Error" not in result.reason
        assert "database connection failed" not in result.reason

        # 技术细节应该在data里
        assert "Internal Server Error" in result.data["internal_error"]
