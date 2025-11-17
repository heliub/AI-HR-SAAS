"""
高情商回复（结束语）

场景名: high_eq_response
模板变量：历史对话、职位信息、HR（AI）最后一句话、招聘方设置的当前职位的问题列表
执行逻辑：CLG1
节点返回结果：
- action为SEND_MESSAGE，message为模型响应的消息
"""
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import NodeExecutor


class HighEQResponseNode(NodeExecutor):
    """高情商回复（结束语）"""
    node_name = "high_eq_response"

    def __init__(self):
        super().__init__(
            scene_name=self.node_name,
            node_name=self.node_name,
        )

    async def _do_execute(self, context: ConversationContext) -> NodeResult:
        """执行节点"""
        # 调用LLM生成高情商结束语
        llm_response = await self.call_llm(context)
        content = llm_response.get("newReply", None) if isinstance(llm_response, dict) else None

        if content is None:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.SUSPEND,
                reason="无法解析有效的高情商回复",
                data=llm_response
            )
        content = str(content).strip()

        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.SEND_MESSAGE,
            message=content,
            data={"message": content}
        )
