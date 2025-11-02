"""
N6: 候选人的回复是否满足设定的要求

场景名: reply_match_question_requirement
模板变量：HR（AI）设定当前正在沟通的问题、历史对话
执行逻辑：CLG1
模型响应结果：{"satisfied": "yes/no"}
节点返回结果：
- 模型响应结果是"YES"，action为NEXT_NODE，next_node为N14节点的名称
- 否则action为SUSPEND
"""
from typing import Dict, Any

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import SimpleLLMNode


class N6RequirementMatchNode(SimpleLLMNode):
    """N6: 候选人的回复是否满足设定的要求"""

    def __init__(self):
        super().__init__(
            node_name="N6",
            scene_name="reply_match_question_requirement"
        )

    async def _parse_llm_response(
        self,
        llm_response: Dict[str, Any],
        context: ConversationContext
    ) -> NodeResult:
        """解析LLM响应"""
        # 获取判断结果
        satisfied = llm_response.get("satisfied", "no").upper()

        if satisfied == "YES":
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["N14"],
                reason="候选人回复满足要求，继续询问下一个问题",
                data={"satisfied": True}
            )
        else:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.SUSPEND,
                reason="候选人回复不满足要求",
                data={"satisfied": False}
            )
