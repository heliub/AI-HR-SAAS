"""
候选人是否申请转人工

场景名：transfer_human_intent
模板变量：候选人最后一条消息
执行逻辑：CLG1
模型响应结果：{"transfer": "yes/no"}
节点返回结果：
- 执行结果为yes，action为SUSPEND
- 否则为action为CONTINUE
"""
from typing import Dict, Any, Union, Optional

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import SimpleLLMNode


class TransferHumanIntentNode(SimpleLLMNode):
    """候选人是否申请转人工"""

    node_name = "transfer_human_intent"
    def __init__(self):
        super().__init__(
            scene_name=self.node_name,
            node_name=self.node_name,
        )

    async def _parse_llm_response(
        self,
        llm_response: Union[Dict[str, Any], str],
        context: ConversationContext
    ) -> NodeResult:
        """解析LLM响应"""
        # 获取模型返回的转人工意图
        transfer = llm_response.get("transfer") if isinstance(llm_response, dict) else None
        
        # 如果无法解析有效转人工意图，返回降级结果
        if transfer is None:
            return self._fallback_result(context, Exception("无法解析有效的转人工意图"), data=llm_response)
        
        transfer = str(transfer).upper()
        # NodeResult的data只存放解析后的模型结果
        data = {
            "transfer": transfer
        }

        # 转人工：中断流程
        if transfer == "YES" or "YES" in transfer:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.SUSPEND,
                reason="候选人申请转人工",
                data=data
            )
        
        # 不转人工：继续情感分析
        if transfer == "NO" or "NO" in transfer:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["candidate_emotion"],  # 继续情感分析
                data=data
            )
        
        # 其他值：返回降级结果
        return self._fallback_result(context, None, data=llm_response)

    def _fallback_result(self, context: ConversationContext, exception: Optional[Exception] = None, data: Optional[Dict[str, Any]] = None) -> NodeResult:
        """降级结果"""
        return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["candidate_emotion"],  # 继续情感分析
                data=data or {},
                is_fallback=True,
                fallback_reason="无法解析有效的转人工意图"
            )
