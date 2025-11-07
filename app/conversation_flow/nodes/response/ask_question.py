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

    def __init__(self):
        super().__init__(
            scene_name="candidate_ask_question",
            node_name="candidate_ask_question"
        )

    async def _parse_llm_response(
        self,
        llm_response: Union[Dict[str, Any], str],
        context: ConversationContext
    ) -> NodeResult:
        """解析LLM响应"""
        # 获取判断结果
        is_question_str = "no"  # 默认值
        question_type = ""
        
        # 如果llm_response是字典，尝试获取is_question和question_type字段
        if isinstance(llm_response, dict):
            is_question_str = llm_response.get("is_question", "no").upper()
            question_type = llm_response.get("question_type", "")
        # 如果是字符串，直接解析
        else:
            content = llm_response.strip()
            # 尝试从自然语言响应中提取是否是问题
            if content.upper().startswith("YES"):
                is_question_str = "YES"
            elif content.upper().startswith("NO"):
                is_question_str = "NO"
            else:
                # 默认为不是问题，以避免误判
                is_question_str = "NO"
            question_type = ""

        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.CONTINUE,
            data={
                "is_question": is_question_str == "YES",
                "question_type": question_type
            }
        )

    def _fallback_result(
        self,
        context: ConversationContext,
        exception: Exception = None
    ) -> NodeResult:
        """
        发问检测降级策略：假定候选人未发问，走闲聊路径

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
