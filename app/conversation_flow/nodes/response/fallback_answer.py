"""
无知识库时兜底回复

场景名: answer_without_knowledge
模板变量：历史对话、候选人最后一条消息
执行逻辑：CLG1
节点返回结果：
- action为SEND_MESSAGE，message为模型响应的消息
"""
from typing import Dict, Any

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import NodeExecutor


class FallbackAnswerNode(NodeExecutor):
    """无知识库兜底回复"""

    def __init__(self):
        super().__init__(
            scene_name="answer_without_knowledge",
            node_name="answer_without_knowledge"
        )

    async def _do_execute(self, context: ConversationContext) -> NodeResult:
        """执行节点"""
        # 调用LLM生成兜底回复
        llm_response = await self.call_llm(context)

        # 处理 llm_response 可能是字典或字符串的情况
        # 根据 answer_without_knowledge.md，输出格式为 {"issue_class": "...", "answer": "str"}
        if isinstance(llm_response, dict):
            # 如果是字典，尝试获取 answer 字段
            content = llm_response.get("answer", "")
        else:
            # 如果是字符串，直接使用
            content = llm_response
        
        content = str(content).strip()

        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.SEND_MESSAGE,
            message=content,
            data={"type": "fallback"}
        )

    def _fallback_result(
        self,
        context: ConversationContext,
        exception: Exception = None
    ) -> NodeResult:
        """
        兜底回复降级策略：返回固定的友好兜底消息

        理由：即使LLM失败，也要给候选人一个友好的回复
        """
        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.SEND_MESSAGE,
            message="感谢您的咨询！我会尽快为您核实相关信息，稍后回复您。如有紧急问题，请联系我们的HR团队。",
            data={
                "type": "fallback",
                "technical_fallback": True,
                "fallback_reason": str(exception) if exception else "unknown"
            }
        )
