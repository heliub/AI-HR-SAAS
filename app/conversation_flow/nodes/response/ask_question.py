"""
N4: 候选人是否发问

场景名：candidate_ask_question
模板变量：候选人最后一条消息、历史对话
执行逻辑：CLG1
节点返回结果：
- 模型响应结果是"YES"，action为CONTINUE，data中is_question=True
- 否则action为CONTINUE，data中is_question=False
"""
from typing import Dict, Any

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import SimpleLLMNode


class AskQuestionNode(SimpleLLMNode):
    """候选人是否发问"""

    def __init__(self):
        super().__init__(
            scene_name="candidate_ask_question",
            node_name="N4"
        )

    async def _parse_llm_response(
        self,
        llm_response: Dict[str, Any],
        context: ConversationContext
    ) -> NodeResult:
        """解析LLM响应"""
        # 获取判断结果
        is_question_str = llm_response.get("is_question", "no").upper()

        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.CONTINUE,
            data={
                "is_question": is_question_str == "YES",
                "question_type": llm_response.get("question_type", "")
            }
        )

    def _fallback_result(
        self,
        context: ConversationContext,
        exception: Exception = None
    ) -> NodeResult:
        """
        N4降级策略：假定候选人未发问，走闲聊路径

        理由：闲聊是最安全的兜底策略
        """
        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.CONTINUE,
            data={
                "is_question": False,
                "question_type": "",
                "fallback": True,
                "fallback_reason": str(exception) if exception else "unknown"
            }
        )
