"""
动态节点执行器

通过节点名称动态执行节点，无需硬编码节点引用
"""
import asyncio
from typing import List, Optional
import structlog

from app.conversation_flow.models import NodeResult, ConversationContext
from app.conversation_flow.node_factory import NodeFactory

logger = structlog.get_logger(__name__)


class DynamicNodeExecutor:
    """
    动态节点执行器
    
    职责：
    - 通过节点名称动态执行节点
    - 不负责流程编排（串行、并行、选择等）
    - 保持简单纯粹
    """
    
    def __init__(self, factory: NodeFactory):
        """
        初始化动态节点执行器
        
        Args:
            factory: 节点工厂
        """
        self.factory = factory
        logger.info("dynamic_node_executor_initialized")
    
    async def execute(
        self,
        node_name: str,
        context: ConversationContext
    ) -> NodeResult:
        """
        通过名称执行单个节点
        
        Args:
            node_name: 节点名称
            context: 会话上下文
            
        Returns:
            节点执行结果
            
        Raises:
            ValueError: 节点不存在
            Exception: 节点执行异常
        """
        
        # 创建节点实例（协程安全）
        node = await self.factory.create_node(node_name)
        # 执行节点
        result = await node.execute(context)
        return result
    
    async def execute_parallel(
        self,
        node_names: List[str],
        context: ConversationContext
    ) -> List[NodeResult]:
        """
        并行执行多个节点
        
        Args:
            node_names: 节点名称列表
            context: 会话上下文
            
        Returns:
            节点执行结果列表
            
        Note:
            - 这是一个便捷方法，用于并行执行
            - 所有节点都会执行，不会短路
            - 如果有节点失败，会抛出异常
        """
        logger.info(
            "executing_nodes_in_parallel",
            node_names=node_names,
            count=len(node_names)
        )
        
        tasks = [self.execute(name, context) for name in node_names]
        results = await asyncio.gather(*tasks)
        
        logger.info(
            "parallel_execution_completed",
            count=len(results),
            actions=[r.action.value for r in results]
        )
        
        return results
    
    def has_node(self, node_name: str) -> bool:
        """
        检查节点是否存在
        
        Args:
            node_name: 节点名称
            
        Returns:
            是否存在
        """
        return self.factory.has_node(node_name)

