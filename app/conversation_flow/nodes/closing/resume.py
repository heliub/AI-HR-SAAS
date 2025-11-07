"""
复聊语

场景名: resume_conversation
模板变量：职位名称、历史对话
执行逻辑：CLG1
节点返回结果：
- action为SEND_MESSAGE，message为模型响应的消息
"""
from typing import Dict, Any

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import NodeExecutor


class ResumeConversationNode(NodeExecutor):
    """复聊语"""

    def __init__(self):
        super().__init__(
            scene_name="resume_conversation",
            node_name="resume_conversation"
        )

    async def _do_execute(self, context: ConversationContext) -> NodeResult:
        """执行节点"""
        # 调用LLM生成复聊语
        llm_response = await self.call_llm(context, parse_json=False)

        # 处理 llm_response 可能是字典或字符串的情况
        # 根据 resume_conversation.md，输出格式为 {"result": }
        if isinstance(llm_response, dict):
            # 如果是字典，尝试获取 result 字段
            content = llm_response.get("result", "")
        else:
            # 如果是字符串，直接使用
            content = llm_response
        
        content = str(content).strip()

        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.SEND_MESSAGE,
            message=content,
            data={"type": "resume_conversation"}
        )
