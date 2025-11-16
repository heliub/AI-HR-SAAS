"""
候选人针对问题的沟通意愿

前置条件：Stage2并且当前询问问题不是判卷问题
场景名：candidate_communication_willingness_for_question
模板变量：历史对话
执行逻辑：CLG1
模型响应结果：{"willing": "yes/no"}
节点返回结果：
- 模型响应结果是"YES"，action为NEXT_NODE，next_node为information_gathering_question节点的名称
- 否则action为SUSPEND
"""
from typing import Dict, Any, Union

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import SimpleLLMNode


class QuestionWillingnessNode(SimpleLLMNode):
    """候选人针对问题的沟通意愿"""

    node_name = "candidate_communication_willingness_for_question"
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
        willing = llm_response.get("result") if isinstance(llm_response, dict) else None
        
        # 如果无法解析有效沟通意愿，返回降级结果
        if willing is None:
            return self._fallback_result(context, Exception("无法解析有效的沟通意愿"), data=llm_response)
        
        # 验证willing值有效性
        willing = str(willing).upper()
        
        # NodeResult的data只存放解析后的模型结果
        data = {
            "willing": willing
        }
        
        # 愿意沟通：继续询问下一个问题
        if willing == "YES":
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["information_gathering_question"],
                reason="候选人愿意沟通，继续询问下一个问题",
                data=data
            )
        
        # 不愿意沟通：中断流程
        if willing == "NO":
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.SUSPEND,
                reason="候选人针对问题的沟通意愿较低",
                data=data
            )
        
        # 其他值：返回降级结果
        return self._fallback_result(context, Exception(f"沟通意愿值不在有效范围内: {willing}"), data=llm_response)
