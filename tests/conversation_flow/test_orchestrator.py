"""
会话流程编排器集成测试

测试完整的会话流程，包括：
- Stage1（开场白阶段）
- Stage2（问题询问阶段）
- Stage3（职位意向阶段）
- 各种边界情况
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime
from typing import List

from app.conversation_flow import (
    ConversationFlowOrchestrator,
    ConversationContext,
    ConversationStage,
    ConversationStatus,
    PositionInfo,
    Message,
    NodeAction,
)


@pytest.fixture
def mock_db_session():
    """Mock数据库会话"""
    # TODO: 实现Mock数据库会话
    # 这里应该使用pytest-asyncio和Mock库创建异步数据库会话
    from unittest.mock import AsyncMock
    return AsyncMock()


@pytest.fixture
def sample_context() -> ConversationContext:
    """创建示例会话上下文"""
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


class TestConversationFlowOrchestrator:
    """会话流程编排器测试"""

    @pytest.mark.asyncio
    async def test_precheck_transfer_human(self, mock_db_session, sample_context):
        """测试：候选人申请转人工"""
        # 修改消息为转人工意图
        sample_context.last_candidate_message = "我想和真人HR沟通"

        orchestrator = ConversationFlowOrchestrator(db=mock_db_session)

        # 注意：这个测试需要Mock LLM响应
        # result = await orchestrator.execute(sample_context)

        # assert result.action == NodeAction.SUSPEND
        # assert "转人工" in result.reason
        # assert "N1" in result.execution_path

    @pytest.mark.asyncio
    async def test_precheck_bad_emotion(self, mock_db_session, sample_context):
        """测试：候选人情感极差"""
        # 修改消息为负面情感
        sample_context.last_candidate_message = "你们公司太垃圾了，不要再联系我！"

        orchestrator = ConversationFlowOrchestrator(db=mock_db_session)

        # 注意：这个测试需要Mock LLM响应
        # result = await orchestrator.execute(sample_context)

        # assert result.action == NodeAction.SUSPEND
        # assert "情感" in result.reason
        # assert "N2" in result.execution_path

    @pytest.mark.asyncio
    async def test_stage1_normal_flow(self, mock_db_session, sample_context):
        """测试：Stage1正常流程"""
        orchestrator = ConversationFlowOrchestrator(db=mock_db_session)

        # 注意：这个测试需要Mock：
        # - N1: 返回非转人工
        # - N2: 返回正常情感
        # - N3: 返回愿意沟通
        # - N4: 返回发问
        # - N9: 返回知识库答案

        # result = await orchestrator.execute(sample_context)

        # assert result.action == NodeAction.SEND_MESSAGE
        # assert result.message is not None
        # assert "N1" in result.execution_path
        # assert "N2" in result.execution_path
        # assert result.total_time_ms > 0

    @pytest.mark.asyncio
    async def test_stage2_question_flow(self, mock_db_session, sample_context):
        """测试：Stage2问题询问流程"""
        # 修改Stage为questioning
        sample_context.conversation_stage = ConversationStage.QUESTIONING
        sample_context.last_candidate_message = "我有3年Python经验"

        orchestrator = ConversationFlowOrchestrator(db=mock_db_session)

        # 注意：这个测试需要Mock：
        # - N1: 非转人工
        # - N2: 正常情感
        # - N15: 路由到问题处理
        # - Response组和Question组并行执行

        # result = await orchestrator.execute(sample_context)

        # assert result.action in [NodeAction.SEND_MESSAGE, NodeAction.NONE]
        # assert "N15" in result.execution_path or "Response" in result.execution_path

    @pytest.mark.asyncio
    async def test_parallel_execution_timing(self, mock_db_session, sample_context):
        """测试：并行执行性能"""
        orchestrator = ConversationFlowOrchestrator(db=mock_db_session)

        # 测试并行执行是否真正提升性能
        # 预期：N1+N2并行执行时间 < N1+N2串行执行时间

        # result = await orchestrator.execute(sample_context)

        # 验证执行时间
        # assert result.total_time_ms < 预期的串行时间


# ============ 使用示例（非测试） ============

async def example_usage():
    """完整的使用示例"""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    # 1. 创建数据库会话
    engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 2. 创建流程编排器
        orchestrator = ConversationFlowOrchestrator(db=session)

        # 3. 构建会话上下文
        context = ConversationContext(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            user_id=uuid4(),
            job_id=uuid4(),
            resume_id=uuid4(),
            conversation_status=ConversationStatus.ONGOING,
            conversation_stage=ConversationStage.GREETING,
            last_candidate_message="你好，请问这个职位的薪资范围是多少？",
            history=[
                Message(sender="ai", content="您好！感谢您的关注。"),
                Message(sender="candidate", content="你好，请问这个职位的薪资范围是多少？")
            ],
            position_info=PositionInfo(
                id=uuid4(),
                name="Python后端工程师",
                description="负责后端系统开发",
                requirements="3年以上Python经验"
            )
        )

        # 4. 执行流程
        result = await orchestrator.execute(context)

        # 5. 处理结果
        print(f"执行动作: {result.action.value}")
        print(f"返回消息: {result.message}")
        print(f"执行路径: {' -> '.join(result.execution_path)}")
        print(f"总耗时: {result.total_time_ms:.2f}ms")

        if result.action == NodeAction.SEND_MESSAGE:
            # 发送消息给候选人
            await send_message_to_candidate(
                conversation_id=context.conversation_id,
                message=result.message
            )

        elif result.action == NodeAction.SUSPEND:
            # 中断流程，通知人工
            await notify_human_agent(
                conversation_id=context.conversation_id,
                reason=result.reason
            )


async def send_message_to_candidate(conversation_id: UUID, message: str):
    """发送消息给候选人（示例函数）"""
    print(f"[发送消息] 会话ID: {conversation_id}")
    print(f"[消息内容] {message}")


async def notify_human_agent(conversation_id: UUID, reason: str):
    """通知人工介入（示例函数）"""
    print(f"[通知人工] 会话ID: {conversation_id}")
    print(f"[原因] {reason}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
