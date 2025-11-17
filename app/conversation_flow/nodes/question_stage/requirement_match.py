"""
候选人的回复是否满足设定的要求

场景名: reply_match_question_requirement
模板变量：HR（AI）设定当前正在沟通的问题、历史对话
执行逻辑：CLG1
模型响应结果：{"satisfied": "yes/no"}
节点返回结果：
- 模型响应结果是"YES"，action为NEXT_NODE，next_node为information_gathering_question节点的名称
- 否则action为SUSPEND
"""
from typing import Dict, Any, Union

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import SimpleLLMNode


class RequirementMatchNode(SimpleLLMNode):
    """候选人的回复是否满足设定的要求"""

    node_name = "reply_match_question_requirement"
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
        # 获取模型返回的满足度
        satisfied = llm_response.get("result") if isinstance(llm_response, dict) else None
        
        # 如果无法解析有效满足度，返回降级结果
        if satisfied is None:
            return self._fallback_result(context, Exception("无法解析有效的满足度"), llm_response)
        
        # 验证satisfied值有效性
        satisfied = str(satisfied).upper()
        
        # NodeResult的data只存放解析后的模型结果
        data = {
            "satisfied": satisfied
        }

        # 满足要求：继续询问下一个问题
        if satisfied == "YES" or "YES" in satisfied:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["information_gathering_question"],
                reason="候选人回复满足要求，继续询问下一个问题",
                data=data
            )
        
        # 候选人未明确回答问题，尝试知识库回复
        if satisfied == "QUESTION" or "QUESTION" in satisfied:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["answer_based_on_knowledge"],
                reason="候选人未明确回答问题，尝试知识库回复",
                data=data
            )
        
        # 不满足要求：中断流程
        if satisfied == "NO" or "NO" in satisfied:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.SUSPEND,
                reason="候选人回复不满足要求",
                data=data
            )
        
        # 其他值：返回降级结果
        return self._fallback_result(context, Exception(f"满足度值不在有效范围内: {satisfied}"), llm_response)
