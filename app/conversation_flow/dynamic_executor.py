"""
动态节点执行器

通过节点名称动态执行节点，无需硬编码节点引用
"""
import asyncio
from typing import List, Optional, Dict
import structlog

from app.conversation_flow.models import NodeResult, ConversationContext
from app.conversation_flow.node_factory import NodeFactory
from app.conversation_flow.models import NodeAction

logger = structlog.get_logger(__name__)


class DynamicNodeExecutor:
    """
    动态节点执行器
    
    职责：
    - 通过节点名称动态执行节点
    - 不负责流程编排（串行、并行、选择等）
    - 保持简单纯粹
    """
    
    def __init__(self):
        self.factory = NodeFactory()
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
        context: ConversationContext,
        timeout: float = 90.0
    ) -> Dict[str, Optional[NodeResult]]:
        """
        并行执行多个节点（带超时和部分成功支持）
        
        Args:
            node_names: 节点名称列表
            context: 会话上下文
            timeout: 超时时间（秒），默认90秒
            
        Returns:
            节点执行结果字典（包含成功、失败和超时的结果），如果节点执行失败，则返回None
            
        Note:
            - 使用 asyncio.wait() 实现更简洁的超时和部分成功处理
            - 超时后已完成的任务结果会被保留
            - 未完成的任务会被标记为超时，不等待清理完成
        """
        logger.info(
            "executing_nodes_in_parallel",
            node_names=node_names,
            count=len(node_names),
            timeout=timeout
        )
        tasks = []
        task_to_name: Dict[asyncio.Task, str] = {}
        for name in node_names:
            task = asyncio.create_task(self.execute(name, context))
            tasks.append(task)
            task_to_name[task] = name
        
        done, pending = await asyncio.wait(
            tasks,
            timeout=timeout,
            return_when=asyncio.ALL_COMPLETED
        )
        
        # 收集结果
        results: Dict[str, Optional[NodeResult]] = {}  
        # 处理已完成的任务
        for task in done:
            node_name = task_to_name[task]
            try:
                result = await task
                results[node_name] = result
            except asyncio.CancelledError:
                # 任务被取消，创建超时结果
                results[node_name] = self._create_timeout_result(node_name, timeout)
            except Exception as e:
                logger.error(
                    "node_execution_failed",
                    node_name=node_name,
                    error=str(e),
                    error_type=type(e).__name__
                )
                results[node_name] = self._create_error_result(node_name, e)
        
        # 取消未完成的任务但不等待清理
        for task in pending:
            node_name = task_to_name[task]
            results[node_name] = self._create_timeout_result(node_name, timeout)
            task.cancel()
            
        return results
    
    def _create_error_result(self, node_name: str, error: Exception) -> NodeResult:
        """
        为执行失败的节点创建错误结果
        
        Args:
            node_name: 节点名称
            error: 异常对象
            
        Returns:
            标记为失败的节点执行结果
        """        
        
        return NodeResult(
            node_name=node_name,
            action=NodeAction.NONE,
            reason=f"节点执行失败: {str(error)}",
            is_fallback=True,
            fallback_reason=f"{type(error).__name__}: {str(error)}"
        )
    
    def _create_timeout_result(self, node_name: str, timeout: float) -> NodeResult:
        """
        为超时的节点创建超时结果
        
        Args:
            node_name: 节点名称
            timeout: 超时时间（秒）
            
        Returns:
            标记为超时的节点执行结果
        """
        
        return NodeResult(
            node_name=node_name,
            action=NodeAction.NONE,
            reason=f"节点执行超时（{timeout}秒）",
            is_fallback=True,
            fallback_reason=f"EXECUTION_TIMEOUT: 超过{timeout}秒未完成"
        )
    
    def has_node(self, node_name: str) -> bool:
        """
        检查节点是否存在
        
        Args:
            node_name: 节点名称
            
        Returns:
            是否存在
        """
        return self.factory.has_node(node_name)

