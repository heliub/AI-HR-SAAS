"""
候选人是否愿意沟通

前置条件：不是Stage2并且不是Stage3
场景名：continue_conversation_with_candidate
模板变量：历史对话
执行逻辑：CLG1
节点返回结果：
- 模型响应结果是"YES"，action为CONTINUE，data中willing=True
- 否则action为NEXT_NODE，next_node为high_eq_response节点的名称，data中willing=False
"""
from typing import Dict, Any

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import SimpleLLMNode


class ContinueConversationNode(SimpleLLMNode):
    """候选人是否愿意沟通"""

    def __init__(self):
        super().__init__(
            scene_name="continue_conversation_with_candidate",
            node_name="continue_conversation_with_candidate"
        )

    async def _parse_llm_response(
        self,
        llm_response: Dict[str, Any],
        context: ConversationContext
    ) -> NodeResult:
        """解析LLM响应"""
        # 获取判断结果
        willing_str = llm_response.get("willing", "no").upper()

        if willing_str == "YES":
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.CONTINUE,
                data={"willing": True}
            )
        else:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["high_eq_response"],  # 跳转到高情商结束语
                reason="候选人沟通意愿较低",
                data={"willing": False}
            )

    def _fallback_result(
        self,
        context: ConversationContext,
        exception: Exception = None
    ) -> NodeResult:
        """
        沟通意愿判断降级策略：假定候选人愿意沟通，继续流程

        理由：默认候选人是善意的，避免技术故障导致误判
        """
        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.CONTINUE,
            data={
                "willing": True,
                "fallback": True,
                "fallback_reason": str(exception) if exception else "unknown"
            }
        )
