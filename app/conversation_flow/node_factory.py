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

logger = structlog.get_logger(__name__)


class NodeFactory:
    """
    节点工厂
    
    统一配置所有节点的创建方式：
    - 无状态节点：单例模式
    - 有状态节点：每次创建（因为需要db session）
    """
    
    # 节点配置：统一配置，避免重复
    # 格式：{节点名称: (节点类, 是否需要db)}
    NODE_CONFIG: Dict[str, tuple[Type[NodeExecutor], bool]] = {
        # 前置检查节点（无状态）
        "transfer_human_intent": (TransferHumanIntentNode, False),
        "candidate_emotion": (EmotionAnalysisNode, False),
        
        # Response组节点
        "continue_conversation_with_candidate": (ContinueConversationNode, False),
        "candidate_ask_question": (AskQuestionNode, False),
        "answer_based_on_knowledge": (KnowledgeAnswerNode, True),  # 需要db
        "answer_without_knowledge": (FallbackAnswerNode, False),
        "casual_conversation": (CasualChatNode, False),
        
        # Question组节点
        "relevance_reply_and_question": (RelevanceCheckNode, False),
        "reply_match_question_requirement": (RequirementMatchNode, False),
        "candidate_communication_willingness_for_question": (QuestionWillingnessNode, False),
        "information_gathering_question": (QuestionHandlerNode, True),  # 需要db
        
        # 结束语节点
        "high_eq_response": (HighEQResponseNode, True),  # 需要db
        "resume_conversation": (ResumeConversationNode, False),
    }
    
    def __init__(self, db: AsyncSession):
        """
        初始化节点工厂
        
        Args:
            db: 数据库会话（用于创建需要db的节点）
        """
        self.db = db
        self._singleton_cache: Dict[str, NodeExecutor] = {}
        self._lock = asyncio.Lock()  # 协程锁，保护单例缓存
        
        logger.info(
            "node_factory_initialized",
            total_nodes=len(self.NODE_CONFIG),
            stateless_nodes=sum(1 for _, needs_db in self.NODE_CONFIG.values() if not needs_db),
            stateful_nodes=sum(1 for _, needs_db in self.NODE_CONFIG.values() if needs_db)
        )
    
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
        
        node_class, needs_db = self.NODE_CONFIG[node_name]
        
        # 无状态节点：单例（使用锁保护，避免协程竞态）
        if not needs_db:
            if node_name in self._singleton_cache:
                return self._singleton_cache[node_name]
            async with self._lock:
                if node_name not in self._singleton_cache:
                    logger.debug("creating_singleton_node", node_name=node_name)
                    self._singleton_cache[node_name] = node_class()
                return self._singleton_cache[node_name]
        
        # 有状态节点：每次创建新实例
        else:
            logger.debug("creating_stateful_node", node_name=node_name)
            return node_class(self.db)
    
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

