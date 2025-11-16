"""
对话回复组执行器

组合节点：沟通意愿判断 -> 发问检测 + 知识库回复（投机式并行） -> 选择最终回复
"""
import asyncio
import structlog

from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.dynamic_executor import DynamicNodeExecutor
from app.conversation_flow.nodes.response.continue_conversation import ContinueConversationNode
from app.conversation_flow.nodes.response.ask_question import AskQuestionNode
from app.conversation_flow.nodes.response.knowledge_answer import KnowledgeAnswerNode
from app.conversation_flow.nodes.response.fallback_answer import FallbackAnswerNode
from app.conversation_flow.nodes.response.casual_chat import CasualChatNode

logger = structlog.get_logger(__name__)


class ResponseGroupExecutor:
    """对话回复组执行器"""
    
    def __init__(self, executor: DynamicNodeExecutor):
        """
        初始化对话回复组执行器
        
        Args:
            executor: 动态节点执行器
        """
        self.executor = executor
    
    async def execute(self, context: ConversationContext) -> NodeResult:
        """
        执行对话回复链
        
        执行流程：
        1. 根据Stage决定是否执行沟通意愿判断
        2. 执行发问检测并根据next_node并行执行后续节点
        3. 根据业务逻辑选择最终结果
        
        Args:
            context: 会话上下文
            
        Returns:
            节点执行结果
        """
        logger.debug(
            "response_group_execution_started",
            stage=context.conversation_stage.value
        )

        if context.is_questioning_stage:
            return NodeResult(node_name="ResponseGroup", action=NodeAction.NONE, reason="跳过沟通意愿判断，直接执行发问检测")
     
        willingness_task = asyncio.create_task(
            self.executor.execute(ContinueConversationNode.node_name, context)
        )
        question_detection_task = asyncio.create_task(
            self.executor.execute(AskQuestionNode.node_name, context)
        )
        willingness_result, question_detection_result = await asyncio.gather(willingness_task,question_detection_task)

        if willingness_result.action == NodeAction.NEXT_NODE and AskQuestionNode.node_name in willingness_result.next_node:
            next_node = question_detection_result
        else:
            next_node = willingness_result
         
        while (next_node and next_node.action == NodeAction.NEXT_NODE):
            next_node = await self.executor.execute(next_node.next_node[0], context)
        return next_node