"""
N11: 陪候选人闲聊

场景名：casual_conversation
模板变量：历史对话、职位信息、HR（AI）最后一句话
执行逻辑：CLG1
节点返回结果：
- action为SEND_MESSAGE，message为模型响应的消息
"""
from typing import Dict, Any

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import NodeExecutor


class CasualChatNode(NodeExecutor):
    """陪候选人闲聊"""

    def __init__(self):
        super().__init__(
            scene_name="casual_conversation",
            node_name="N11"
        )

    async def _do_execute(self, context: ConversationContext) -> NodeResult:
        """执行节点"""
        # 调用LLM生成闲聊回复
        llm_response = await self.call_llm(context, parse_json=False)

        content = llm_response.get("content", "").strip()

        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.SEND_MESSAGE,
            message=content,
            data={"type": "casual_chat"}
        )
