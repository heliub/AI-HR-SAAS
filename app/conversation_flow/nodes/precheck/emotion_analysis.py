"""
候选人情感分析

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
from typing import Dict, Any, Union, Optional

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import SimpleLLMNode


class EmotionAnalysisNode(SimpleLLMNode):
    """候选人情感分析"""
    node_name = "candidate_emotion"
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
        # 获取模型返回的分数和原因
        score = llm_response.get("分数") if isinstance(llm_response, dict) else None
        reason = llm_response.get("原因") if isinstance(llm_response, dict) else None
        
        # 如果无法解析有效分数，返回降级结果
        if score is None:
            return self._fallback_result(context, Exception("无法解析有效的情感分数或原因"), data=llm_response)
        
        # 验证分数有效性
        try:
            score = int(score)
        except (ValueError, TypeError):
            return self._fallback_result(context, Exception("情感分数格式错误"), data=llm_response)

        # NodeResult的data只存放解析后的模型结果
        data = {
            "emotion_score": score,
            "emotion_reason": reason
        }

        # 分数为3：情感极差，中断流程
        if score == 3:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.SUSPEND,
                reason=f"候选人情感极差(分数={score}): {reason}",
                data=data
            )

        # 分数为2：情感一般，需要发送高情商结束语
        if score == 2:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["high_eq_response"],  # 发送高情商结束语
                reason=f"候选人情感一般(分数={score})，发送高情商结束语",
                data=data
            )

        # 分数为0或1：情感正常，继续后续流程
        if score in [0, 1]:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                # 继续Response组（沟通意愿判断）和Question组（问题处理）
                next_node=["continue_conversation_with_candidate", "information_gathering"],
                reason=f"候选人情感正常(分数={score})，继续主流程",
                data=data
            )
        
        # 其他分数值：返回降级结果
        return self._fallback_result(context, None, data=llm_response)

    def _fallback_result(self, context: ConversationContext, exception: Optional[Exception] = None, data: Optional[Dict[str, Any]] = None) -> NodeResult:
        """降级结果"""
        return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["continue_conversation_with_candidate", "information_gathering"],  # 发送高情商结束语
                data=data or {},
                is_fallback=True,
                fallback_reason="无法解析有效的情感分数"
            )