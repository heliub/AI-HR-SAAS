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

    def __init__(self):
        super().__init__(
            scene_name="reply_match_question_requirement",
            node_name="reply_match_question_requirement"
        )

    async def _parse_llm_response(
        self,
        llm_response: Union[Dict[str, Any], str],
        context: ConversationContext
    ) -> NodeResult:
        """解析LLM响应"""
        # 获取判断结果
        satisfied = "no"  # 默认值
        
        # 如果llm_response是字典，尝试获取satisfied字段
        if isinstance(llm_response, dict):
            satisfied = llm_response.get("satisfied", "no").upper()
        # 如果是字符串，直接解析
        else:
            content = llm_response.strip()
            # 尝试从自然语言响应中提取满足度
            if content.upper().startswith("YES"):
                satisfied = "YES"
            elif content.upper().startswith("NO"):
                satisfied = "NO"
            else:
                # 默认为不满足，以避免误判
                satisfied = "NO"

        if satisfied == "YES":
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["information_gathering_question"],
                reason="候选人回复满足要求，继续询问下一个问题",
                data={"satisfied": True}
            )
        else:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.SUSPEND,
                reason="候选人回复不满足要求",
                data={"satisfied": False}
            )
