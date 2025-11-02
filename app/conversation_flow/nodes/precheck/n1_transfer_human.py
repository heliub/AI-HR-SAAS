"""
N1: 候选人是否申请转人工

场景名：transfer_human_intent
模板变量：候选人最后一条消息
执行逻辑：CLG1
模型响应结果：{"transfer": "yes/no"}
节点返回结果：
- 执行结果为yes，action为SUSPEND
- 否则为action为CONTINUE
"""
from typing import Dict, Any

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import SimpleLLMNode


class N1TransferHumanIntentNode(SimpleLLMNode):
    """N1: 候选人是否申请转人工"""

    def __init__(self):
        super().__init__(
            node_name="N1",
            scene_name="transfer_human_intent"
        )

    async def _parse_llm_response(
        self,
        llm_response: Dict[str, Any],
        context: ConversationContext
    ) -> NodeResult:
        """解析LLM响应"""
        transfer = llm_response.get("transfer", "no").lower()

        if transfer == "yes":
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.SUSPEND,
                reason="候选人申请转人工",
                data={"transfer_intent": True}
            )
        else:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.CONTINUE,
                data={"transfer_intent": False}
            )

    def _fallback_result(
        self,
        context: ConversationContext,
        exception: Exception = None
    ) -> NodeResult:
        """
        N1降级策略：假定候选人不转人工，继续流程

        理由：宁可AI多聊几句，也不要因为技术故障误转人工
        """
        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.CONTINUE,
            data={
                "transfer_intent": False,
                "fallback": True,
                "fallback_reason": str(exception) if exception else "unknown"
            }
        )
