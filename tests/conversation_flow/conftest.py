"""
测试fixtures和Mock工具
"""
import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.conversation_flow.models import (
    ConversationContext,
    ConversationStage,
    ConversationStatus,
    PositionInfo,
    Message,
)


@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.flush = AsyncMock()
    return db


@pytest.fixture
def sample_context():
    """创建标准测试上下文"""
    return ConversationContext(
        conversation_id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        job_id=uuid4(),
        resume_id=uuid4(),
        conversation_status=ConversationStatus.ONGOING,
        conversation_stage=ConversationStage.GREETING,
        last_candidate_message="你好，我想了解一下这个职位",
        history=[
            Message(
                sender="ai",
                content="您好！感谢您关注我们的Python工程师职位。",
                message_type="greeting",
                created_at=datetime.now()
            ),
            Message(
                sender="candidate",
                content="你好，我想了解一下这个职位",
                message_type="question",
                created_at=datetime.now()
            )
        ],
        position_info=PositionInfo(
            id=uuid4(),
            name="Python后端工程师",
            description="负责后端系统开发，要求熟悉Python、FastAPI、数据库等技术栈",
            requirements="3年以上Python开发经验"
        )
    )


@pytest.fixture
def stage2_context(sample_context):
    """Stage2（问题阶段）上下文"""
    sample_context.conversation_stage = ConversationStage.QUESTIONING
    sample_context.current_question_id = uuid4()
    sample_context.current_question_content = "请介绍一下你的Python项目经验"
    return sample_context


class MockLLMResponse:
    """Mock LLM响应"""

    @staticmethod
    def transfer_human_yes():
        """N1: 转人工"""
        return {"transfer": "yes"}

    @staticmethod
    def transfer_human_no():
        """N1: 不转人工"""
        return {"transfer": "no"}

    @staticmethod
    def emotion_score(score: int, reason: str = "正常"):
        """N2: 情感分析"""
        return {"分数": score, "原因": reason}

    @staticmethod
    def willing_yes():
        """N3: 愿意沟通"""
        return {"willing": "YES"}

    @staticmethod
    def willing_no():
        """N3: 不愿意沟通"""
        return {"willing": "NO"}

    @staticmethod
    def is_question_yes():
        """N4: 候选人发问了"""
        return {"is_question": "YES", "question_type": "salary"}

    @staticmethod
    def is_question_no():
        """N4: 候选人未发问"""
        return {"is_question": "NO"}

    @staticmethod
    def text_response(content: str):
        """通用文本响应"""
        return {"content": content}

    @staticmethod
    def invalid_json():
        """无效的JSON"""
        return {"content": "这不是有效的JSON"}

    @staticmethod
    def incomplete_json():
        """不完整的JSON"""
        return {"content": '{"transfer": '}


@pytest.fixture
def mock_llm_caller():
    """Mock LLM调用器"""
    with patch('app.conversation_flow.nodes.base.get_llm_caller') as mock:
        llm_caller = MagicMock()
        llm_caller.call_with_scene = AsyncMock()
        mock.return_value = llm_caller
        yield llm_caller


@pytest.fixture
def mock_job_knowledge_service():
    """Mock知识库服务"""
    with patch('app.conversation_flow.nodes.response.n9_knowledge_answer.JobKnowledgeService') as mock:
        service = MagicMock()
        service.search_for_conversation = AsyncMock()
        mock.return_value = service
        yield service


@pytest.fixture
def mock_job_question_service():
    """Mock问题服务"""
    with patch('app.services.job_question_service.JobQuestionService') as mock:
        service = MagicMock()
        service.get_questions_by_job = AsyncMock()
        mock.return_value = service
        yield service
