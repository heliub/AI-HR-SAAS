"""
候选人回复和问题相关性

前置条件：Stage2并且当前询问问题是判卷问题
场景名：relevance_reply_and_question
模板变量：HR（AI）设定当前正在沟通的问题、候选人最后一条消息
执行逻辑：CLG1
模型响应结果：{"relevance": "A/B/C/D/E"}
节点返回结果：
- 模型响应结果是A、D、E，action为SUSPEND
- 如果是B，action为NEXT_NODE，next_node为reply_match_question_requirement节点的名称
- 如果是C，action为NEXT_NODE，next_node为information_gathering_question节点的名称
"""
from typing import Dict, Any

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import SimpleLLMNode


class RelevanceCheckNode(SimpleLLMNode):
    """候选人回复和问题相关性检查"""

    def __init__(self):
        super().__init__(
            scene_name="relevance_reply_and_question",
            node_name="relevance_reply_and_question"
        )

    async def _parse_llm_response(
        self,
        llm_response: Dict[str, Any],
        context: ConversationContext
    ) -> NodeResult:
        """解析LLM响应"""
        # 获取相关性等级
        relevance = llm_response.get("relevance", "E").upper()

        # A、D、E：异常情况，中断流程
        if relevance in ["A", "D", "E"]:
            reason_map = {
                "A": "候选人拒绝回答",
                "D": "候选人回复异常或包含敏感内容",
                "E": "无法判断相关性"
            }
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.SUSPEND,
                reason=reason_map.get(relevance, f"相关性检查异常: {relevance}"),
                data={"relevance": relevance}
            )

        # B：相关且有效，继续满足度检查
        elif relevance == "B":
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["reply_match_question_requirement"],
                reason="候选人回复相关且有效",
                data={"relevance": relevance}
            )

        # C：答非所问，继续询问下一个问题
        elif relevance == "C":
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["information_gathering_question"],
                reason="候选人答非所问，继续询问下一个问题",
                data={"relevance": relevance}
            )

        # 其他情况：默认中断
        else:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.SUSPEND,
                reason=f"未知的相关性等级: {relevance}",
                data={"relevance": relevance}
            )
