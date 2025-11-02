"""
测试ConversationContext的输入验证

验证__post_init__方法的各种验证逻辑
"""
import pytest
from uuid import uuid4
from datetime import datetime
from app.conversation_flow.models import (
    ConversationContext,
    ConversationStage,
    ConversationStatus,
    PositionInfo,
    Message,
)


class TestContextValidation:
    """测试Context输入验证"""

    def test_valid_context_passes(self):
        """有效的Context应该通过验证"""
        context = ConversationContext(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            user_id=uuid4(),
            job_id=uuid4(),
            resume_id=uuid4(),
            conversation_status=ConversationStatus.ONGOING,
            conversation_stage=ConversationStage.GREETING,
            last_candidate_message="你好",
            history=[Message(sender="candidate", content="你好", created_at=datetime.now())],
            position_info=PositionInfo(id=uuid4(), name="Python工程师")
        )
        # 如果没有抛出异常，说明验证通过
        assert context.conversation_id is not None

    def test_missing_conversation_id_raises_error(self):
        """conversation_id为None应该抛出错误"""
        with pytest.raises(ValueError, match="conversation_id不能为空"):
            ConversationContext(
                conversation_id=None,  # ❌
                tenant_id=uuid4(),
                user_id=uuid4(),
                job_id=uuid4(),
                resume_id=uuid4(),
                conversation_status=ConversationStatus.ONGOING,
                conversation_stage=ConversationStage.GREETING,
                last_candidate_message="你好",
                history=[Message(sender="candidate", content="你好", created_at=datetime.now())],
                position_info=PositionInfo(id=uuid4(), name="Python工程师")
            )

    def test_invalid_conversation_status_type_raises_error(self):
        """conversation_status不是枚举类型应该抛出错误"""
        with pytest.raises(ValueError, match="conversation_status必须是ConversationStatus枚举类型"):
            ConversationContext(
                conversation_id=uuid4(),
                tenant_id=uuid4(),
                user_id=uuid4(),
                job_id=uuid4(),
                resume_id=uuid4(),
                conversation_status="ongoing",  # ❌ 字符串而不是枚举
                conversation_stage=ConversationStage.GREETING,
                last_candidate_message="你好",
                history=[Message(sender="candidate", content="你好", created_at=datetime.now())],
                position_info=PositionInfo(id=uuid4(), name="Python工程师")
            )

    def test_invalid_conversation_stage_type_raises_error(self):
        """conversation_stage不是枚举类型应该抛出错误"""
        with pytest.raises(ValueError, match="conversation_stage必须是ConversationStage枚举类型"):
            ConversationContext(
                conversation_id=uuid4(),
                tenant_id=uuid4(),
                user_id=uuid4(),
                job_id=uuid4(),
                resume_id=uuid4(),
                conversation_status=ConversationStatus.ONGOING,
                conversation_stage="greeting",  # ❌ 字符串而不是枚举
                last_candidate_message="你好",
                history=[Message(sender="candidate", content="你好", created_at=datetime.now())],
                position_info=PositionInfo(id=uuid4(), name="Python工程师")
            )

    def test_empty_last_candidate_message_raises_error(self):
        """last_candidate_message为空字符串应该抛出错误"""
        with pytest.raises(ValueError, match="last_candidate_message不能为空"):
            ConversationContext(
                conversation_id=uuid4(),
                tenant_id=uuid4(),
                user_id=uuid4(),
                job_id=uuid4(),
                resume_id=uuid4(),
                conversation_status=ConversationStatus.ONGOING,
                conversation_stage=ConversationStage.GREETING,
                last_candidate_message="   ",  # ❌ 只有空格
                history=[Message(sender="candidate", content="你好", created_at=datetime.now())],
                position_info=PositionInfo(id=uuid4(), name="Python工程师")
            )

    def test_whitespace_last_candidate_message_raises_error(self):
        """last_candidate_message只有空白字符应该抛出错误"""
        with pytest.raises(ValueError, match="last_candidate_message不能为空"):
            ConversationContext(
                conversation_id=uuid4(),
                tenant_id=uuid4(),
                user_id=uuid4(),
                job_id=uuid4(),
                resume_id=uuid4(),
                conversation_status=ConversationStatus.ONGOING,
                conversation_stage=ConversationStage.GREETING,
                last_candidate_message="\t\n  ",  # ❌ 制表符和换行符
                history=[Message(sender="candidate", content="你好", created_at=datetime.now())],
                position_info=PositionInfo(id=uuid4(), name="Python工程师")
            )

    def test_empty_history_raises_error(self):
        """history为空列表应该抛出错误"""
        with pytest.raises(ValueError, match="history不能为空"):
            ConversationContext(
                conversation_id=uuid4(),
                tenant_id=uuid4(),
                user_id=uuid4(),
                job_id=uuid4(),
                resume_id=uuid4(),
                conversation_status=ConversationStatus.ONGOING,
                conversation_stage=ConversationStage.GREETING,
                last_candidate_message="你好",
                history=[],  # ❌ 空列表
                position_info=PositionInfo(id=uuid4(), name="Python工程师")
            )

    def test_none_history_raises_error(self):
        """history为None应该抛出错误"""
        with pytest.raises(ValueError, match="history不能为空"):
            ConversationContext(
                conversation_id=uuid4(),
                tenant_id=uuid4(),
                user_id=uuid4(),
                job_id=uuid4(),
                resume_id=uuid4(),
                conversation_status=ConversationStatus.ONGOING,
                conversation_stage=ConversationStage.GREETING,
                last_candidate_message="你好",
                history=None,  # ❌ None
                position_info=PositionInfo(id=uuid4(), name="Python工程师")
            )

    def test_missing_position_info_in_stage2_raises_error(self):
        """Stage2时position_info为None应该抛出错误"""
        with pytest.raises(ValueError, match="Stage2必须有position_info"):
            ConversationContext(
                conversation_id=uuid4(),
                tenant_id=uuid4(),
                user_id=uuid4(),
                job_id=uuid4(),
                resume_id=uuid4(),
                conversation_status=ConversationStatus.ONGOING,
                conversation_stage=ConversationStage.QUESTIONING,  # Stage2
                last_candidate_message="请介绍一下你的项目经验",
                history=[Message(sender="ai", content="请介绍一下你的项目经验", created_at=datetime.now())],
                position_info=None  # ❌ Stage2但没有position_info
            )

    def test_position_info_can_be_none_in_stage1(self):
        """Stage1时position_info可以为None（虽然不推荐）"""
        context = ConversationContext(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            user_id=uuid4(),
            job_id=uuid4(),
            resume_id=uuid4(),
            conversation_status=ConversationStatus.ONGOING,
            conversation_stage=ConversationStage.GREETING,  # Stage1
            last_candidate_message="你好",
            history=[Message(sender="candidate", content="你好", created_at=datetime.now())],
            position_info=None  # ✅ Stage1可以没有position_info
        )
        assert context.position_info is None

    def test_missing_current_question_in_questioning_stage_raises_error(self):
        """QUESTIONING阶段时缺少current_question_id应该抛出错误"""
        with pytest.raises(ValueError, match="QUESTIONING阶段必须有current_question_id"):
            ConversationContext(
                conversation_id=uuid4(),
                tenant_id=uuid4(),
                user_id=uuid4(),
                job_id=uuid4(),
                resume_id=uuid4(),
                conversation_status=ConversationStatus.ONGOING,
                conversation_stage=ConversationStage.QUESTIONING,
                last_candidate_message="我的项目经验是...",
                history=[Message(sender="candidate", content="我的项目经验是...", created_at=datetime.now())],
                position_info=PositionInfo(id=uuid4(), name="Python工程师"),
                current_question_id=None,  # ❌ QUESTIONING阶段但没有问题ID
                current_question_content="请介绍一下你的项目经验"
            )

    def test_missing_current_question_content_in_questioning_stage_raises_error(self):
        """QUESTIONING阶段时缺少current_question_content应该抛出错误"""
        with pytest.raises(ValueError, match="QUESTIONING阶段必须有current_question_content"):
            ConversationContext(
                conversation_id=uuid4(),
                tenant_id=uuid4(),
                user_id=uuid4(),
                job_id=uuid4(),
                resume_id=uuid4(),
                conversation_status=ConversationStatus.ONGOING,
                conversation_stage=ConversationStage.QUESTIONING,
                last_candidate_message="我的项目经验是...",
                history=[Message(sender="candidate", content="我的项目经验是...", created_at=datetime.now())],
                position_info=PositionInfo(id=uuid4(), name="Python工程师"),
                current_question_id=uuid4(),
                current_question_content=None  # ❌ QUESTIONING阶段但没有问题内容
            )

    def test_all_uuid_fields_can_be_none_initially(self):
        """某些UUID字段可以为None（比如还没开始问问题）"""
        context = ConversationContext(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            user_id=uuid4(),
            job_id=uuid4(),
            resume_id=uuid4(),
            conversation_status=ConversationStatus.ONGOING,
            conversation_stage=ConversationStage.GREETING,
            last_candidate_message="你好",
            history=[Message(sender="candidate", content="你好", created_at=datetime.now())],
            position_info=PositionInfo(id=uuid4(), name="Python工程师"),
            current_question_id=None,  # ✅ GREETING阶段可以没有问题
            current_question_content=None
        )
        assert context.current_question_id is None
        assert context.current_question_content is None


class TestMessageValidation:
    """测试Message模型的验证"""

    def test_valid_message(self):
        """有效的Message应该通过验证"""
        message = Message(
            sender="candidate",
            content="你好",
            message_type="greeting",
            created_at=datetime.now()
        )
        assert message.sender == "candidate"

    def test_message_with_minimal_fields(self):
        """Message最少需要sender和content"""
        message = Message(
            sender="ai",
            content="欢迎",
            created_at=datetime.now()
        )
        assert message.message_type is None  # 可以没有message_type

    def test_message_created_at_defaults_to_now(self):
        """created_at应该有默认值"""
        message = Message(
            sender="candidate",
            content="测试"
        )
        # 检查created_at是否在最近1秒内
        time_diff = (datetime.now() - message.created_at).total_seconds()
        assert time_diff < 1.0


class TestPositionInfoValidation:
    """测试PositionInfo模型的验证"""

    def test_valid_position_info(self):
        """有效的PositionInfo"""
        position = PositionInfo(
            id=uuid4(),
            name="Python工程师",
            description="负责后端开发",
            requirements="3年以上Python经验"
        )
        assert position.name == "Python工程师"

    def test_position_info_minimal_fields(self):
        """PositionInfo只需要id和name"""
        position = PositionInfo(
            id=uuid4(),
            name="Java工程师"
        )
        assert position.description is None
        assert position.requirements is None
