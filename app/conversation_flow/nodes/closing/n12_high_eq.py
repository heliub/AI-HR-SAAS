"""
N12：高情商回复（结束语）

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


class N12HighEQResponseNode(NodeExecutor):
    """N12: 高情商回复（结束语）"""

    def __init__(self, db: AsyncSession = None):
        super().__init__(
            node_name="N12",
            scene_name="high_eq_response",
            db=db
        )

    async def _do_execute(self, context: ConversationContext) -> NodeResult:
        """执行节点"""
        # 调用LLM生成高情商结束语
        llm_response = await self.call_llm(context, parse_json=False)

        content = llm_response.get("content", "").strip()

        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.SEND_MESSAGE,
            message=content,
            data={"type": "high_eq_closing"}
        )
