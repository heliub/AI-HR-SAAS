"""
会话流程编排模块

提供候选人AI会话的流程编排功能，包括：
- 节点执行器：单个节点的执行逻辑
- 节点组执行器：多个节点的组合执行
- 流程编排器：整体流程的调度和控制

核心概念：
1. 节点（Node）：最小执行单元，负责单一职责的LLM调用或业务逻辑
2. 节点组（NodeGroup）：按职责组合的节点集合，如Response组、Question组
3. 流程编排器（Orchestrator）：负责节点/节点组的并行调度和结果选择

设计原则：
- 高内聚：节点按职责分组，每个节点只负责单一功能
- 高并发：采用投机式并行执行，最大化利用异步特性
- 高可用：技术异常自动重试，业务异常正常流转
- 高扩展：新增节点只需继承基类，实现核心逻辑即可

使用示例：
```python
from app.conversation_flow import ConversationFlowOrchestrator
from app.conversation_flow.models import ConversationContext, PositionInfo

# 创建流程编排器
orchestrator = ConversationFlowOrchestrator(db=db_session)

# 构建会话上下文
context = ConversationContext(
    conversation_id=conversation.id,
    tenant_id=tenant_id,
    user_id=user_id,
    job_id=job_id,
    resume_id=resume_id,
    conversation_status=ConversationStatus.ONGOING,
    conversation_stage=ConversationStage.GREETING,
    last_candidate_message="你好，我想了解一下这个职位",
    history=[...],
    position_info=PositionInfo(...)
)

# 执行流程
result = await orchestrator.execute(context)

# 处理结果
if result.action == NodeAction.SEND_MESSAGE:
    await send_message_to_candidate(result.message)
elif result.action == NodeAction.SUSPEND:
    await notify_human_agent(result.reason)
```
"""
from .models import (
    ConversationStage,
    ConversationStatus,
    QuestionStatus,
    NodeAction,
    Message,
    NodeResult,
    FlowResult,
    PositionInfo,
    ConversationContext,
)
from .orchestrator import ConversationFlowOrchestrator
from .nodes.base import NodeExecutor, SimpleLLMNode

__all__ = [
    # 枚举和常量
    "ConversationStage",
    "ConversationStatus",
    "QuestionStatus",
    "NodeAction",
    # 数据模型
    "Message",
    "NodeResult",
    "FlowResult",
    "PositionInfo",
    "ConversationContext",
    # 核心组件
    "ConversationFlowOrchestrator",
    "NodeExecutor",
    "SimpleLLMNode",
]
