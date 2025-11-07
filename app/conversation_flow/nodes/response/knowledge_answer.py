"""
基于知识库回复求职者

场景名: answer_based_on_knowledge
模板变量：职位信息、知识库信息、历史对话、候选人最后一条消息
执行逻辑：额外查询职位对应的知识库信息，和入参中上下文中已存在的其他模板变量，继续执行CLG1
节点返回结果：
- 模型响应结果是"not_found"，action为CONTINUE，data中found=False
- 否则action为SEND_MESSAGE，message为模型响应的消息，data中found=True
"""
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import NodeExecutor


class KnowledgeAnswerNode(NodeExecutor):
    """基于知识库回复求职者"""

    def __init__(self, db: AsyncSession):
        super().__init__(
            scene_name="answer_based_on_knowledge",
            node_name="answer_based_on_knowledge",
            db=db
        )

    async def _do_execute(self, context: ConversationContext) -> NodeResult:
        """执行节点"""
        from app.services.job_knowledge_service import JobKnowledgeService

        # 1. 查询知识库（知识库回复内部搜索，高内聚原则）
        knowledge_service = JobKnowledgeService(self.db)

        knowledge_results = await knowledge_service.search_for_conversation(
            query=context.last_candidate_message,
            job_id=context.job_id,
            tenant_id=context.tenant_id,
            conversation_id=context.conversation_id,
            top_k=3
        )

        if not knowledge_results:
            # 没有找到知识库
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.CONTINUE,
                data={"found": False, "reason": "no_knowledge_found"}
            )

        # 2. 创建临时context副本，包含知识库结果（避免修改原context，保证并发安全）
        from dataclasses import replace
        temp_context = replace(context, knowledge_base_results=knowledge_results)

        # 3. 调用LLM生成回复（使用临时context）
        llm_response = await self.call_llm(temp_context, parse_json=False)

        # 4. 检查是否为"not_found"
        content = llm_response.strip()

        if content.lower() == "not_found" or "not_found" in content.lower():
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.CONTINUE,
                data={"found": False, "reason": "llm_not_found"}
            )

        # 5. 返回回复消息
        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.SEND_MESSAGE,
            message=content,
            data={
                "found": True,
                "knowledge_count": len(knowledge_results)
            }
        )
