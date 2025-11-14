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

    def __init__(self):
        super().__init__(
            scene_name="casual_conversation",
            node_name="casual_conversation"
        )

    async def _do_execute(self, context: ConversationContext) -> NodeResult:
        """执行节点"""
        # 调用LLM生成闲聊回复
        llm_response = await self.call_llm(context)

        # 处理 llm_response 可能是字典或字符串的情况
        # 根据 casual_conversation.md，输出格式为 {"newReply":str}
        if isinstance(llm_response, dict):
            # 如果是字典，尝试获取 newReply 字段
            content = llm_response.get("newReply", "")
        else:
            # 如果是字符串，直接使用
            content = llm_response
        
        content = str(content).strip()

        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.SEND_MESSAGE,
            message=content,
            data={"type": "casual_chat"}
        )
