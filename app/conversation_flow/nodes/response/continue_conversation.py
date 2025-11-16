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
from typing import Dict, Any, Union

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import SimpleLLMNode


class ContinueConversationNode(SimpleLLMNode):
    """候选人是否愿意沟通"""

    node_name = "continue_conversation_with_candidate"
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
        # 获取模型返回的沟通意愿
        willing = llm_response.get("willing") if isinstance(llm_response, dict) else None
        
        # 如果无法解析有效沟通意愿，返回降级结果
        if willing is None:
            return self._fallback_result(context, Exception("无法解析有效的沟通意愿"), llm_response)
        
        # 验证willing_str值有效性
        willing = str(willing).upper()
        
        # NodeResult的data只存放解析后的模型结果
        data = {
            "willing": willing
        }

        # 愿意沟通：继续发问检测
        if willing == "YES":
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["candidate_ask_question"],  # 继续发问检测
                data=data
            )
        
        # 不愿意沟通：跳转到高情商结束语
        if willing == "NO":
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["high_eq_response"],  # 跳转到高情商结束语
                reason="候选人沟通意愿较低",
                data=data
            )
        
        # 其他值：返回降级结果
        return self._fallback_result(context, Exception(f"沟通意愿值不在有效范围内: {willing}"), llm_response)
