"""
N2: 候选人情感分析

场景名: candidate_emotion
模板变量：历史对话
执行逻辑：CLG1
模型响应结果：{
    "分数": "",
    "原因": ""
}
节点返回结果：
- 分数为0和1，action为CONTINUE，data中包含score和reason
- 分数为2，action为CONTINUE，data中标记需要发送结束语
- 分数为3，action为SUSPEND
"""
from typing import Dict, Any

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import SimpleLLMNode


class N2EmotionAnalysisNode(SimpleLLMNode):
    """N2: 候选人情感分析"""

    def __init__(self):
        super().__init__(
            node_name="N2",
            scene_name="candidate_emotion"
        )

    async def _parse_llm_response(
        self,
        llm_response: Dict[str, Any],
        context: ConversationContext
    ) -> NodeResult:
        """解析LLM响应"""
        # 获取分数和原因
        score = int(llm_response.get("分数", 0))
        reason = llm_response.get("原因", "")

        # 分数为3：情感极差，中断流程
        if score == 3:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.SUSPEND,
                reason=f"候选人情感极差(分数={score}): {reason}",
                data={"emotion_score": score, "emotion_reason": reason}
            )

        # 分数为2：情感一般，需要发送高情商结束语
        elif score == 2:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.CONTINUE,
                data={
                    "emotion_score": score,
                    "emotion_reason": reason,
                    "need_closing": True  # 标记需要发送结束语
                }
            )

        # 分数为0或1：情感正常，继续后续流程
        else:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.CONTINUE,
                data={
                    "emotion_score": score,
                    "emotion_reason": reason,
                    "need_closing": False
                }
            )

    def _fallback_result(
        self,
        context: ConversationContext,
        exception: Exception = None
    ) -> NodeResult:
        """
        N2降级策略：假定候选人情感正常(分数1)，继续流程

        理由：除非明确负面，否则继续沟通，避免技术故障导致误判
        """
        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.CONTINUE,
            data={
                "emotion_score": 1,
                "emotion_reason": "技术故障，假定情感正常",
                "need_closing": False,
                "fallback": True,
                "fallback_reason": str(exception) if exception else "unknown"
            }
        )
