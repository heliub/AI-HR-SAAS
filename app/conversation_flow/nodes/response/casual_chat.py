"""
陪候选人闲聊

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

    node_name = "casual_conversation"
    def __init__(self):
        super().__init__(
            scene_name=self.node_name,
            node_name=self.node_name,
        )

    async def _do_execute(self, context: ConversationContext) -> NodeResult:
        """执行节点"""
        # 调用LLM生成闲聊回复
        llm_response = await self.call_llm(context)

        content = llm_response.get("newReply", None) if isinstance(llm_response, dict) else None  
        
        if content is None:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.SUSPEND,
                reason="无法解析有效的闲聊回复",
                data=llm_response
            )

        content = str(content).strip()

        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.SEND_MESSAGE,
            message=content,
            data={"message": content}
        )
