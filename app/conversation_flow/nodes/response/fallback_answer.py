"""
无知识库时兜底回复

场景名: answer_without_knowledge
模板变量：历史对话、候选人最后一条消息
执行逻辑：CLG1
节点返回结果：
- action为SEND_MESSAGE，message为模型响应的消息
"""
from typing import Dict, Any

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import NodeExecutor


class FallbackAnswerNode(NodeExecutor):
    """无知识库兜底回复"""

    node_name = "answer_without_knowledge"
    def __init__(self):
        super().__init__(
            scene_name=self.node_name,
            node_name=self.node_name,
        )

    async def _do_execute(self, context: ConversationContext) -> NodeResult:
        """执行节点"""
        # 调用LLM生成兜底回复
        llm_response = await self.call_llm(context)
        content = llm_response.get("answer", None) if isinstance(llm_response, dict) else None
        issue_class = llm_response.get("issue_class", None) if isinstance(llm_response, dict) else None
        if content is None:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.SUSPEND,
                reason="无法解析有效的兜底回复",
                data=llm_response
            )
        content = str(content).strip()

        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.SEND_MESSAGE,
            message=content,
            data={"message": content, "issue_class": issue_class}
        )
