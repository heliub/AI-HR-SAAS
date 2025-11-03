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
from typing import Dict, Any

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import SimpleLLMNode


class QuestionWillingnessNode(SimpleLLMNode):
    """候选人针对问题的沟通意愿"""

    def __init__(self):
        super().__init__(
            scene_name="candidate_communication_willingness_for_question",
            node_name="candidate_communication_willingness_for_question"
        )

    async def _parse_llm_response(
        self,
        llm_response: Dict[str, Any],
        context: ConversationContext
    ) -> NodeResult:
        """解析LLM响应"""
        # 获取判断结果
        willing = llm_response.get("willing", "no").upper()
        
        # 如果没有willing字段，尝试从content中解析
        if "willing" not in llm_response and "content" in llm_response:
            content = llm_response["content"]
            # 尝试从自然语言响应中提取意愿
            if content.upper().startswith("YES"):
                willing = "YES"
            elif content.upper().startswith("NO"):
                willing = "NO"
            else:
                # 默认为愿意，以避免误判
                willing = "YES"

        if willing == "YES":
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["information_gathering_question"],
                reason="候选人愿意沟通，继续询问下一个问题",
                data={"willing": True}
            )
        else:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.SUSPEND,
                reason="候选人针对问题的沟通意愿较低",
                data={"willing": False}
            )
