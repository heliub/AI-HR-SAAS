"""
测试N9节点的并发安全性

验证N9在并行执行时不会修改原始context，避免并发问题
"""
import pytest
import asyncio
from uuid import uuid4
from app.conversation_flow.nodes.response import N9KnowledgeAnswerNode
from app.conversation_flow.models import NodeAction


class TestN9ConcurrentSafety:
    """测试N9并发安全"""

    @pytest.mark.asyncio
    async def test_n9_does_not_modify_original_context(
        self, sample_context, mock_db, mock_job_knowledge_service
    ):
        """N9执行后，原始context不应该被修改"""
        node = N9KnowledgeAnswerNode(mock_db)

        # Mock知识库搜索结果
        mock_knowledge = [
            {"question": "薪资范围", "answer": "15-25K"},
            {"question": "工作地点", "answer": "北京"}
        ]
        mock_job_knowledge_service.search_for_conversation.return_value = mock_knowledge

        # 保存原始的knowledge_base_results（应该是None）
        original_knowledge = sample_context.knowledge_base_results

        # 执行N9
        result = await node.execute(sample_context)

        # 验证：原始context没有被修改
        assert sample_context.knowledge_base_results == original_knowledge, \
            "N9不应该修改原始context的knowledge_base_results"
        assert sample_context.knowledge_base_results is None, \
            "原始context的knowledge_base_results应该保持为None"

        # 验证：节点正常执行
        assert result.action == NodeAction.SEND_MESSAGE or result.action == NodeAction.CONTINUE

    @pytest.mark.asyncio
    async def test_n9_concurrent_execution_no_interference(
        self, mock_db, mock_job_knowledge_service
    ):
        """两个N9实例并发执行，不应该互相干扰"""
        from app.conversation_flow.models import (
            ConversationContext, ConversationStage, ConversationStatus,
            PositionInfo, Message
        )
        from datetime import datetime

        node = N9KnowledgeAnswerNode(mock_db)

        # 创建两个不同的context
        context1 = ConversationContext(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            user_id=uuid4(),
            job_id=uuid4(),
            resume_id=uuid4(),
            conversation_status=ConversationStatus.ONGOING,
            conversation_stage=ConversationStage.GREETING,
            last_candidate_message="薪资是多少",
            history=[Message(sender="candidate", content="薪资是多少", created_at=datetime.now())],
            position_info=PositionInfo(id=uuid4(), name="职位1")
        )

        context2 = ConversationContext(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            user_id=uuid4(),
            job_id=uuid4(),
            resume_id=uuid4(),
            conversation_status=ConversationStatus.ONGOING,
            conversation_stage=ConversationStage.GREETING,
            last_candidate_message="工作地点在哪",
            history=[Message(sender="candidate", content="工作地点在哪", created_at=datetime.now())],
            position_info=PositionInfo(id=uuid4(), name="职位2")
        )

        # Mock不同的知识库结果
        call_count = [0]

        async def mock_search(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # 第1次调用返回职位1的知识库
                return [{"question": "薪资", "answer": "15-25K"}]
            else:
                # 第2次调用返回职位2的知识库
                return [{"question": "地点", "answer": "北京"}]

        mock_job_knowledge_service.search_for_conversation.side_effect = mock_search

        # 并发执行
        result1, result2 = await asyncio.gather(
            node.execute(context1),
            node.execute(context2)
        )

        # 验证：两个context都没有被修改
        assert context1.knowledge_base_results is None
        assert context2.knowledge_base_results is None

        # 验证：都成功执行
        assert result1.node_name == "N9"
        assert result2.node_name == "N9"

    @pytest.mark.asyncio
    async def test_n9_uses_replace_to_create_temp_context(
        self, sample_context, mock_db, mock_job_knowledge_service
    ):
        """验证N9使用dataclasses.replace创建临时context"""
        node = N9KnowledgeAnswerNode(mock_db)

        mock_knowledge = [{"question": "测试", "answer": "答案"}]
        mock_job_knowledge_service.search_for_conversation.return_value = mock_knowledge

        # 给LLM caller打补丁，验证传入的context有knowledge_base_results
        with_knowledge_context = None

        async def mock_call_llm(context, **kwargs):
            nonlocal with_knowledge_context
            with_knowledge_context = context
            return "测试回复"

        node.call_llm = mock_call_llm

        await node.execute(sample_context)

        # 验证：传给LLM的context有knowledge_base_results
        assert with_knowledge_context is not None
        assert with_knowledge_context.knowledge_base_results == mock_knowledge

        # 验证：但原始context没有
        assert sample_context.knowledge_base_results is None

        # 验证：是两个不同的对象
        assert with_knowledge_context is not sample_context

    @pytest.mark.asyncio
    async def test_n9_no_knowledge_found(
        self, sample_context, mock_db, mock_job_knowledge_service
    ):
        """没有找到知识库时，应该返回CONTINUE，不修改context"""
        node = N9KnowledgeAnswerNode(mock_db)

        # Mock: 没有找到知识库
        mock_job_knowledge_service.search_for_conversation.return_value = []

        result = await node.execute(sample_context)

        # 验证：返回CONTINUE
        assert result.action == NodeAction.CONTINUE
        assert result.data["found"] is False

        # 验证：没有修改原始context
        assert sample_context.knowledge_base_results is None

    @pytest.mark.asyncio
    async def test_n9_stress_test_100_concurrent_calls(
        self, mock_db, mock_job_knowledge_service
    ):
        """压力测试：100个并发调用，验证无数据竞争"""
        from app.conversation_flow.models import (
            ConversationContext, ConversationStage, ConversationStatus,
            PositionInfo, Message
        )
        from datetime import datetime

        node = N9KnowledgeAnswerNode(mock_db)

        # Mock知识库返回不同结果
        async def mock_search(*args, **kwargs):
            await asyncio.sleep(0.01)  # 模拟网络延迟
            # 返回包含调用信息的唯一知识库
            return [{"question": f"Q-{id(kwargs)}", "answer": f"A-{id(kwargs)}"}]

        mock_job_knowledge_service.search_for_conversation.side_effect = mock_search

        # 创建100个context
        contexts = []
        for i in range(100):
            ctx = ConversationContext(
                conversation_id=uuid4(),
                tenant_id=uuid4(),
                user_id=uuid4(),
                job_id=uuid4(),
                resume_id=uuid4(),
                conversation_status=ConversationStatus.ONGOING,
                conversation_stage=ConversationStage.GREETING,
                last_candidate_message=f"问题{i}",
                history=[Message(sender="candidate", content=f"问题{i}", created_at=datetime.now())],
                position_info=PositionInfo(id=uuid4(), name=f"职位{i}")
            )
            contexts.append(ctx)

        # 并发执行100次
        results = await asyncio.gather(*[node.execute(ctx) for ctx in contexts])

        # 验证：所有context都没有被修改
        for ctx in contexts:
            assert ctx.knowledge_base_results is None, \
                f"Context {ctx.conversation_id} 的knowledge_base_results被意外修改"

        # 验证：所有结果都返回了
        assert len(results) == 100
        for result in results:
            assert result.node_name == "N9"
