"""
候选人是否发问

场景名：candidate_ask_question
模板变量：候选人最后一条消息、历史对话
执行逻辑：CLG1
节点返回结果：
- 模型响应结果是"YES"，action为CONTINUE，data中is_question=True
- 否则action为CONTINUE，data中is_question=False
"""
from typing import Dict, Any, Union

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import SimpleLLMNode


class AskQuestionNode(SimpleLLMNode):
    """候选人是否发问"""

    node_name = "candidate_ask_question"
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
        # 获取模型返回的是否问题
        is_question = llm_response.get("result") if isinstance(llm_response, dict) else None
        
        # 如果无法解析有效的是否问题，返回降级结果
        if is_question is None:
            return self._fallback_result(context, Exception("无法解析有效的是否问题"), llm_response)

        is_question = str(is_question).upper()
        # NodeResult的data只存放解析后的模型结果
        data = {
            "is_question": is_question
        }
        
        # 是问题：使用知识库回答
        if is_question == "YES" or "YES" in is_question:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["answer_based_on_knowledge"],
                data=data
            )
        
        # 不是问题：继续闲聊
        if is_question == "NO" or "NO" in is_question:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["casual_conversation"],
                data=data
            )
        
        # 其他值：返回降级结果
        return self._fallback_result(context, Exception(f"是否问题值不在有效范围内: {is_question}"), llm_response)

