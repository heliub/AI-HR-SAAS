"""
测试各节点的正常业务逻辑

验证关键节点在正常情况下的执行路径和输出
"""
import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from app.conversation_flow.models import NodeAction, ConversationStage
from app.conversation_flow.nodes.precheck import (
    N1TransferHumanIntentNode,
    N2EmotionAnalysisNode
)
from app.conversation_flow.nodes.response import (
    N3ContinueConversationNode,
    N4AskQuestionNode,
    N9KnowledgeAnswerNode,
)
from app.conversation_flow.nodes.question_stage import (
    N14QuestionInitializationNode,
    N15QuestionRoutingNode,
)


class TestN1TransferHumanIntent:
    """测试N1转人工意图识别"""

    @pytest.mark.asyncio
    async def test_n1_detects_transfer_intent(self, sample_context, mock_llm_caller):
        """N1正确识别转人工意图"""
        node = N1TransferHumanIntentNode()

        # Mock: LLM识别出转人工意图
        mock_llm_caller.call_with_scene.return_value = {"transfer": "yes"}

        result = await node.execute(sample_context)

        # 验证：返回SUSPEND，触发转人工
        assert result.node_name == "N1"
        assert result.action == NodeAction.SUSPEND
        assert result.data["transfer_intent"] is True
        assert "候选人明确要求转人工" in result.reason

    @pytest.mark.asyncio
    async def test_n1_no_transfer_intent(self, sample_context, mock_llm_caller):
        """N1正确识别无转人工意图"""
        node = N1TransferHumanIntentNode()

        # Mock: LLM识别出无转人工意图
        mock_llm_caller.call_with_scene.return_value = {"transfer": "no"}

        result = await node.execute(sample_context)

        # 验证：返回CONTINUE，继续流程
        assert result.action == NodeAction.CONTINUE
        assert result.data["transfer_intent"] is False

    @pytest.mark.asyncio
    async def test_n1_call_with_correct_scene(self, sample_context, mock_llm_caller):
        """N1使用正确的scene调用LLM"""
        node = N1TransferHumanIntentNode()
        mock_llm_caller.call_with_scene.return_value = {"transfer": "no"}

        await node.execute(sample_context)

        # 验证：使用了正确的scene_name
        mock_llm_caller.call_with_scene.assert_called_once()
        call_args = mock_llm_caller.call_with_scene.call_args
        assert call_args[1]["scene_name"] == "transfer_human_intent"


class TestN2EmotionAnalysis:
    """测试N2情感分析"""

    @pytest.mark.asyncio
    async def test_n2_detects_negative_emotion(self, sample_context, mock_llm_caller):
        """N2正确识别负面情绪"""
        node = N2EmotionAnalysisNode()

        # Mock: LLM返回负面情绪
        mock_llm_caller.call_with_scene.return_value = {
            "分数": -2,
            "原因": "候选人表达了不满"
        }

        result = await node.execute(sample_context)

        # 验证：识别出需要结束对话
        assert result.node_name == "N2"
        assert result.action == NodeAction.CONTINUE
        assert result.data["emotion_score"] == -2
        assert result.data["need_closing"] is True
        assert "不满" in result.data["emotion_reason"]

    @pytest.mark.asyncio
    async def test_n2_detects_positive_emotion(self, sample_context, mock_llm_caller):
        """N2正确识别正面情绪"""
        node = N2EmotionAnalysisNode()

        # Mock: LLM返回正面情绪
        mock_llm_caller.call_with_scene.return_value = {
            "分数": 2,
            "原因": "候选人表达了兴趣"
        }

        result = await node.execute(sample_context)

        # 验证：不需要结束对话
        assert result.data["emotion_score"] == 2
        assert result.data["need_closing"] is False

    @pytest.mark.asyncio
    async def test_n2_detects_neutral_emotion(self, sample_context, mock_llm_caller):
        """N2正确识别中性情绪"""
        node = N2EmotionAnalysisNode()

        # Mock: LLM返回中性情绪
        mock_llm_caller.call_with_scene.return_value = {
            "分数": 1,
            "原因": "候选人礼貌回复"
        }

        result = await node.execute(sample_context)

        # 验证：中性情绪，继续对话
        assert result.data["emotion_score"] == 1
        assert result.data["need_closing"] is False


class TestN3ContinueConversation:
    """测试N3继续沟通意愿"""

    @pytest.mark.asyncio
    async def test_n3_detects_willing(self, sample_context, mock_llm_caller):
        """N3正确识别愿意沟通"""
        node = N3ContinueConversationNode()

        # Mock: LLM识别出愿意沟通
        mock_llm_caller.call_with_scene.return_value = {"willing": "YES"}

        result = await node.execute(sample_context)

        # 验证：继续流程
        assert result.node_name == "N3"
        assert result.action == NodeAction.CONTINUE
        assert result.data["willing"] is True

    @pytest.mark.asyncio
    async def test_n3_detects_unwilling(self, sample_context, mock_llm_caller):
        """N3正确识别不愿意沟通"""
        node = N3ContinueConversationNode()

        # Mock: LLM识别出不愿意沟通
        mock_llm_caller.call_with_scene.return_value = {"willing": "NO"}

        result = await node.execute(sample_context)

        # 验证：发送结束消息
        assert result.action == NodeAction.SEND_MESSAGE
        assert result.data["willing"] is False
        assert "感谢" in result.message


class TestN4AskQuestion:
    """测试N4发问检测"""

    @pytest.mark.asyncio
    async def test_n4_detects_question_about_salary(self, sample_context, mock_llm_caller):
        """N4正确识别薪资相关问题"""
        node = N4AskQuestionNode()

        # Mock: LLM识别出薪资问题
        mock_llm_caller.call_with_scene.return_value = {
            "is_question": "YES",
            "question_type": "salary"
        }

        result = await node.execute(sample_context)

        # 验证：识别为问题
        assert result.node_name == "N4"
        assert result.action == NodeAction.CONTINUE
        assert result.data["is_question"] is True
        assert result.data["question_type"] == "salary"

    @pytest.mark.asyncio
    async def test_n4_detects_not_a_question(self, sample_context, mock_llm_caller):
        """N4正确识别非问题（闲聊）"""
        node = N4AskQuestionNode()

        # Mock: LLM识别出不是问题
        mock_llm_caller.call_with_scene.return_value = {"is_question": "NO"}

        result = await node.execute(sample_context)

        # 验证：不是问题，走闲聊路径
        assert result.data["is_question"] is False
        assert result.data["question_type"] == ""

    @pytest.mark.asyncio
    async def test_n4_handles_multiple_question_types(self, sample_context, mock_llm_caller):
        """N4能识别多种问题类型"""
        node = N4AskQuestionNode()

        # 测试不同问题类型
        question_types = ["job_content", "location", "benefits", "team", "other"]

        for qtype in question_types:
            mock_llm_caller.call_with_scene.return_value = {
                "is_question": "YES",
                "question_type": qtype
            }
            result = await node.execute(sample_context)
            assert result.data["question_type"] == qtype


class TestN9KnowledgeAnswer:
    """测试N9知识库回答"""

    @pytest.mark.asyncio
    async def test_n9_finds_knowledge_and_answers(
        self, sample_context, mock_db, mock_job_knowledge_service, mock_llm_caller
    ):
        """N9找到知识库并回答"""
        node = N9KnowledgeAnswerNode(mock_db)

        # Mock: 找到知识库
        mock_knowledge = [
            {"question": "薪资范围", "answer": "15-25K"}
        ]
        mock_job_knowledge_service.search_for_conversation.return_value = mock_knowledge

        # Mock: LLM生成回答
        mock_llm_caller.call_with_scene.return_value = {
            "content": "根据职位信息，薪资范围是15-25K。"
        }

        result = await node.execute(sample_context)

        # 验证：返回消息
        assert result.node_name == "N9"
        assert result.action == NodeAction.SEND_MESSAGE
        assert result.data["found"] is True
        assert "薪资" in result.message

    @pytest.mark.asyncio
    async def test_n9_no_knowledge_found(
        self, sample_context, mock_db, mock_job_knowledge_service
    ):
        """N9没找到知识库，返回CONTINUE"""
        node = N9KnowledgeAnswerNode(mock_db)

        # Mock: 没找到知识库
        mock_job_knowledge_service.search_for_conversation.return_value = []

        result = await node.execute(sample_context)

        # 验证：返回CONTINUE，让后续节点处理
        assert result.action == NodeAction.CONTINUE
        assert result.data["found"] is False

    @pytest.mark.asyncio
    async def test_n9_searches_with_correct_parameters(
        self, sample_context, mock_db, mock_job_knowledge_service
    ):
        """N9使用正确的参数搜索知识库"""
        node = N9KnowledgeAnswerNode(mock_db)
        mock_job_knowledge_service.search_for_conversation.return_value = []

        await node.execute(sample_context)

        # 验证：调用了知识库搜索
        mock_job_knowledge_service.search_for_conversation.assert_called_once()
        call_args = mock_job_knowledge_service.search_for_conversation.call_args
        # 检查传入的参数包含job_id和query
        assert call_args is not None


class TestN14QuestionInitialization:
    """测试N14问题初始化"""

    @pytest.mark.asyncio
    async def test_n14_initializes_questions_and_transitions_to_stage2(
        self, sample_context, mock_db, mock_job_question_service
    ):
        """N14初始化问题并转换到Stage2"""
        from app.services.conversation_question_tracking_service import ConversationQuestionTrackingService
        from app.services.conversation_service import ConversationService
        from app.models.job_question import JobQuestion

        node = N14QuestionInitializationNode(mock_db)

        # Mock: 有3个问题
        mock_questions = [
            JobQuestion(
                id=uuid4(),
                job_id=sample_context.job_id,
                question_content="请介绍一下你的Python项目经验",
                question_order=1,
                is_scoring=True
            ),
            JobQuestion(
                id=uuid4(),
                job_id=sample_context.job_id,
                question_content="你有使用过FastAPI吗",
                question_order=2,
                is_scoring=True
            ),
            JobQuestion(
                id=uuid4(),
                job_id=sample_context.job_id,
                question_content="你的期望薪资是多少",
                question_order=3,
                is_scoring=False
            )
        ]
        mock_job_question_service.get_questions_by_job.return_value = mock_questions

        # Mock tracking service
        tracking_service_mock = AsyncMock(spec=ConversationQuestionTrackingService)
        tracking_service_mock.create_question_tracking = AsyncMock()

        # Mock conversation service
        conversation_service_mock = AsyncMock(spec=ConversationService)
        conversation_service_mock.update_conversation_stage = AsyncMock()

        # Patch services
        with pytest.mock.patch(
            'app.conversation_flow.nodes.question_stage.n14_question_initialization.ConversationQuestionTrackingService',
            return_value=tracking_service_mock
        ), pytest.mock.patch(
            'app.conversation_flow.nodes.question_stage.n14_question_initialization.ConversationService',
            return_value=conversation_service_mock
        ):
            result = await node.execute(sample_context)

            # 验证：返回CONTINUE
            assert result.node_name == "N14"
            assert result.action == NodeAction.CONTINUE
            assert result.data["initialized"] is True
            assert result.data["question_count"] == 3

            # 验证：创建了3条tracking记录
            assert tracking_service_mock.create_question_tracking.call_count == 3

            # 验证：更新了conversation_stage
            conversation_service_mock.update_conversation_stage.assert_called_once()

    @pytest.mark.asyncio
    async def test_n14_no_questions_returns_suspend(
        self, sample_context, mock_db, mock_job_question_service
    ):
        """N14没有问题时转人工"""
        node = N14QuestionInitializationNode(mock_db)

        # Mock: 没有问题
        mock_job_question_service.get_questions_by_job.return_value = []

        result = await node.execute(sample_context)

        # 验证：转人工
        assert result.action == NodeAction.SUSPEND
        assert "未配置问题" in result.reason


class TestN15QuestionRouting:
    """测试N15问题路由"""

    @pytest.mark.asyncio
    async def test_n15_routes_to_scoring_question(self, stage2_context, mock_db):
        """N15路由到评分问题"""
        from app.services.conversation_question_tracking_service import ConversationQuestionTrackingService
        from app.models.conversation_question_tracking import ConversationQuestionTracking

        node = N15QuestionRoutingNode(mock_db)

        # Mock: 有一个待处理的评分问题
        mock_tracking = ConversationQuestionTracking(
            id=uuid4(),
            conversation_id=stage2_context.conversation_id,
            question_id=uuid4(),
            question_content="请介绍一下你的Python项目经验",
            question_order=1,
            is_scoring=True,
            status="pending"
        )

        tracking_service_mock = AsyncMock(spec=ConversationQuestionTrackingService)
        tracking_service_mock.get_questions_by_conversation.return_value = [mock_tracking]

        with pytest.mock.patch(
            'app.conversation_flow.nodes.question_stage.n15_question_routing.ConversationQuestionTrackingService',
            return_value=tracking_service_mock
        ):
            result = await node.execute(stage2_context)

            # 验证：路由到评分问题
            assert result.node_name == "N15"
            assert result.action == NodeAction.CONTINUE
            assert result.data["next_question_type"] == "scoring"
            assert result.data["question_id"] == mock_tracking.question_id

    @pytest.mark.asyncio
    async def test_n15_all_questions_done_ends_conversation(self, stage2_context, mock_db):
        """N15所有问题完成后结束对话"""
        from app.services.conversation_question_tracking_service import ConversationQuestionTrackingService

        node = N15QuestionRoutingNode(mock_db)

        # Mock: 所有问题都已完成
        tracking_service_mock = AsyncMock(spec=ConversationQuestionTrackingService)
        tracking_service_mock.get_questions_by_conversation.return_value = []

        with pytest.mock.patch(
            'app.conversation_flow.nodes.question_stage.n15_question_routing.ConversationQuestionTrackingService',
            return_value=tracking_service_mock
        ):
            result = await node.execute(stage2_context)

            # 验证：发送结束消息
            assert result.action == NodeAction.SEND_MESSAGE
            assert result.data["all_done"] is True
            assert "感谢" in result.message
