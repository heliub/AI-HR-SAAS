"""
节点工厂

负责创建和管理节点实例：
- 无状态节点：单例模式，全局复用（协程安全）
- 有状态节点：每次创建新实例
"""
import asyncio
from typing import Dict, Type, Callable
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.conversation_flow.nodes.base import NodeExecutor

# 导入所有节点
from app.conversation_flow.nodes.precheck import (
    TransferHumanIntentNode,
    EmotionAnalysisNode
)
from app.conversation_flow.nodes.response import (
    ContinueConversationNode,
    AskQuestionNode,
    KnowledgeAnswerNode,
    FallbackAnswerNode,
    CasualChatNode
)
from app.conversation_flow.nodes.question_stage import (
    RelevanceCheckNode,
    RequirementMatchNode,
    QuestionWillingnessNode,
    QuestionHandlerNode
)
from app.conversation_flow.nodes.closing import (
    HighEQResponseNode,
    ResumeConversationNode
)
from app.conversation_flow.groups.question_group import QuestionGroupExecutor
from app.conversation_flow.groups.response_group import ResponseGroupExecutor

logger = structlog.get_logger(__name__)


class NodeFactory:
    """
    节点工厂
    
    统一配置所有节点的创建方式：
    """
    
    # 节点配置：统一配置，避免重复
    NODE_CONFIG: Dict[str, Type[NodeExecutor]] = {
        # 前置检查节点（无状态）
        "transfer_human_intent": TransferHumanIntentNode,
        "candidate_emotion": EmotionAnalysisNode,
        
        # Response组节点
        "continue_conversation_with_candidate": ContinueConversationNode,
        "candidate_ask_question": AskQuestionNode,
        "answer_based_on_knowledge": KnowledgeAnswerNode,
        "answer_without_knowledge": FallbackAnswerNode,
        "casual_conversation": CasualChatNode,
        
        # Question组节点
        "relevance_reply_and_question": RelevanceCheckNode,
        "reply_match_question_requirement": RequirementMatchNode,
        "candidate_communication_willingness_for_question": QuestionWillingnessNode,
        "information_gathering_question": QuestionHandlerNode,
        
        # 结束语节点
        "high_eq_response": HighEQResponseNode,
        "resume_conversation": ResumeConversationNode,

        "question_group": QuestionGroupExecutor,
        "response_group": ResponseGroupExecutor,
    }
    
    def __init__(self):
        """
        初始化节点工厂
        
        """
        self._singleton_cache: Dict[str, NodeExecutor] = {}
        self._lock = asyncio.Lock()  # 协程锁，保护单例缓存
    
    async def create_node(self, node_name: str) -> NodeExecutor:
        """
        创建节点实例（协程安全）
        
        Args:
            node_name: 节点名称
            
        Returns:
            节点实例
            
        Raises:
            ValueError: 节点名称不存在
        """
        if node_name not in self.NODE_CONFIG:
            raise ValueError(
                f"Unknown node: {node_name}. "
                f"Available nodes: {list(self.NODE_CONFIG.keys())}"
            )
        
        node_class = self.NODE_CONFIG[node_name]
        
        if node_name in self._singleton_cache:
            return self._singleton_cache[node_name]
        async with self._lock:
            if node_name not in self._singleton_cache:
                logger.debug("creating_singleton_node", node_name=node_name)
                self._singleton_cache[node_name] = node_class()
            return self._singleton_cache[node_name]
            
        
    
    def has_node(self, node_name: str) -> bool:
        """
        检查节点是否存在
        
        Args:
            node_name: 节点名称
            
        Returns:
            是否存在
        """
        return node_name in self.NODE_CONFIG
    
    def get_all_node_names(self) -> list[str]:
        """
        获取所有节点名称
        
        Returns:
            节点名称列表
        """
        return list(self.NODE_CONFIG.keys())

