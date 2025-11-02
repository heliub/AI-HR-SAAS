# 会话流程编排模块 - 快速开始指南

## 📦 安装依赖

确保已安装以下依赖（应该已包含在项目requirements.txt中）：

```bash
pip install sqlalchemy asyncpg structlog
```

## 🚀 5分钟快速集成

### 第一步：导入模块

```python
from app.conversation_flow import (
    ConversationFlowOrchestrator,
    ConversationContext,
    ConversationStage,
    ConversationStatus,
    PositionInfo,
    Message,
    NodeAction
)
from sqlalchemy.ext.asyncio import AsyncSession
```

### 第二步：在你的API接口中集成

```python
from fastapi import APIRouter, Depends
from app.database import get_db

router = APIRouter()

@router.post("/candidate-conversations/{conversation_id}/reply")
async def handle_candidate_message(
    conversation_id: str,
    message: str,
    db: AsyncSession = Depends(get_db)
):
    """处理候选人消息"""

    # 1. 从数据库加载会话信息
    conversation = await load_conversation(db, conversation_id)
    job = await load_job(db, conversation.job_id)
    resume = await load_resume(db, conversation.resume_id)
    history = await load_message_history(db, conversation_id)

    # 2. 构建会话上下文
    context = ConversationContext(
        conversation_id=conversation.id,
        tenant_id=conversation.tenant_id,
        user_id=conversation.user_id,
        job_id=conversation.job_id,
        resume_id=conversation.resume_id,
        conversation_status=ConversationStatus(conversation.status),
        conversation_stage=ConversationStage(conversation.stage),
        last_candidate_message=message,
        history=[
            Message(
                sender=msg.sender,
                content=msg.content,
                message_type=msg.message_type,
                created_at=msg.created_at
            )
            for msg in history
        ],
        position_info=PositionInfo(
            id=job.id,
            name=job.name,
            description=job.description,
            requirements=job.requirements
        )
    )

    # 3. 执行流程编排
    orchestrator = ConversationFlowOrchestrator(db=db)
    result = await orchestrator.execute(context)

    # 4. 处理执行结果
    if result.action == NodeAction.SEND_MESSAGE:
        # 发送AI回复给候选人
        await save_message(db, conversation_id, "ai", result.message)
        return {
            "status": "success",
            "action": "send_message",
            "message": result.message,
            "execution_time_ms": result.total_time_ms
        }

    elif result.action == NodeAction.SUSPEND:
        # 暂停AI，转人工介入
        await update_conversation_status(db, conversation_id, "suspended")
        await notify_hr_agent(conversation_id, result.reason)
        return {
            "status": "success",
            "action": "suspend",
            "reason": result.reason,
            "message": "已转人工客服处理"
        }

    elif result.action == NodeAction.NONE:
        # Stage转换场景（如Stage1->Stage2, Stage2->Stage3）
        # 这种情况下通常不需要发送消息，只是内部状态转换
        return {
            "status": "success",
            "action": "stage_transition",
            "new_stage": context.conversation_stage.value
        }

    elif result.action == NodeAction.TERMINATE:
        # 终止会话（目前设计中未使用，预留）
        await update_conversation_status(db, conversation_id, "terminated")
        return {
            "status": "success",
            "action": "terminate"
        }
```

### 第三步：辅助函数示例

```python
async def load_conversation(db: AsyncSession, conversation_id: str):
    """从数据库加载会话"""
    from app.services.conversation_service import ConversationService
    service = ConversationService(db)
    return await service.get_conversation(conversation_id)

async def load_job(db: AsyncSession, job_id: str):
    """加载职位信息"""
    from app.services.job_service import JobService
    service = JobService(db)
    return await service.get_job(job_id)

async def load_resume(db: AsyncSession, resume_id: str):
    """加载简历信息"""
    from app.services.resume_service import ResumeService
    service = ResumeService(db)
    return await service.get_resume(resume_id)

async def load_message_history(db: AsyncSession, conversation_id: str, limit: int = 20):
    """加载最近的消息历史"""
    from app.services.message_service import MessageService
    service = MessageService(db)
    return await service.get_recent_messages(conversation_id, limit)

async def save_message(db: AsyncSession, conversation_id: str, sender: str, content: str):
    """保存消息到数据库"""
    from app.services.message_service import MessageService
    service = MessageService(db)
    await service.create_message(
        conversation_id=conversation_id,
        sender=sender,
        content=content,
        message_type="text"
    )
    await db.commit()

async def update_conversation_status(db: AsyncSession, conversation_id: str, status: str):
    """更新会话状态"""
    from app.services.conversation_service import ConversationService
    service = ConversationService(db)
    await service.update_status(conversation_id, status)
    await db.commit()

async def notify_hr_agent(conversation_id: str, reason: str):
    """通知HR人工介入（发送通知、邮件等）"""
    # 实现具体的通知逻辑，如：
    # - 发送企业微信/钉钉通知
    # - 发送邮件
    # - 更新任务队列
    print(f"[通知HR] 会话ID: {conversation_id}, 原因: {reason}")
```

## 🔍 执行流程说明

### Stage1（greeting - 开场白阶段）

**候选人消息**: "你好，我想了解一下这个职位"

**执行路径**: N1 → N2 → N3 → N4 → N9（知识库回复）

**并行优化**:
- N1 + N2 并行执行（前置检查）
- N4 + N9 并行执行（投机式）

**预期响应时间**: 2-3秒（比串行快50%）

### Stage2（questioning - 问题询问阶段）

**候选人消息**: "我有3年Python经验"

**执行路径**: N1 → N2 → [Response组 || Question组] → 根据结果选择

**并行优化**:
- N1 + N2 并行
- Response组 + Question组 并行（投机式）

**预期响应时间**: 4-5秒（比串行快33%）

### Stage3（intention - 职位意向阶段）

**候选人消息**: "我对这个职位很感兴趣"

**执行路径**: N1 → N2 → Response组

**预期响应时间**: 2-3秒

## 🛡️ 异常处理

### 技术异常（自动重试）

```python
# LLM调用失败、网络超时等技术异常，系统会自动重试3次
# 重试间隔：1秒、2秒、4秒（指数退避）
```

### 业务异常（正常流转）

```python
# 例如：N5判断答案不相关（C类），直接流转到N14继续下一题
# 不触发重试机制，这是正常的业务逻辑
```

### 降级处理

```python
# 如果3次重试都失败，会返回兜底结果：
# - 前置检查失败：假定正常情感、非转人工
# - LLM节点失败：使用N10兜底回复
```

## 📊 性能监控

所有执行结果都包含详细的性能指标：

```python
result = await orchestrator.execute(context)

print(f"执行动作: {result.action.value}")
print(f"执行路径: {' → '.join(result.execution_path)}")
print(f"总耗时: {result.total_time_ms:.2f}ms")
print(f"元数据: {result.metadata}")
```

## 🔧 配置说明

所有LLM调用的配置（模型、温度等）在 `app/ai/prompts/prompt_config.py` 中定义：

```python
PROMPT_CONFIG = {
    "transfer_human_intent": {
        "provider": "volcengine",
        "model": "doubao-1.5-pro-32k-250115",
        "temperature": 0.1,
        "top_p": 0.1,
        "system": "你是一个AI助手...",
        "prompt": "transfer_human_intent.md"
    },
    # ... 其他场景配置
}
```

**注意**: 修改配置后需要重启应用才能生效（配置在启动时加载）。

## 🐛 调试技巧

### 启用详细日志

```python
import structlog

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG)
)
```

### 查看执行路径

```python
result = await orchestrator.execute(context)
print("执行路径:", " → ".join(result.execution_path))
# 输出示例: N1 → N2 → N3 → N4 → N9
```

### 检查节点数据

```python
print("节点数据:", result.metadata.get("node_data"))
# 输出示例: {"is_question": True, "emotion_score": 8}
```

## ⚠️ 常见问题

### Q1: Stage没有自动转换？

**原因**: N14节点负责Stage转换，只有在问题阶段才会自动推进Stage。

**解决**: 确保 `conversation_stage` 正确设置，且数据库中有对应的JobQuestion记录。

### Q2: 知识库回复总是失败？

**原因**: 可能是知识库中没有相关内容，或者知识库服务异常。

**解决**:
- N9节点会自动搜索知识库（内部封装，无需外部调用）
- 检查数据库中是否有对应职位的知识库记录
- 检查JobKnowledgeService是否正常工作
- 查看日志中的知识库搜索结果

### Q3: 并行执行没有提速？

**原因**: 可能是LLM provider的并发限制，或者数据库连接池不足。

**解决**:
- 检查LLM provider的QPS限制
- 增加数据库连接池大小
- 监控实际的并行执行时间

## 📚 更多文档

- **完整架构**: `app/conversation_flow/README.md`
- **实现细节**: `docs/claude/conversation_flow_implementation.md`
- **任务清单**: `app/conversation_flow/TODO.md`
- **最终总结**: `docs/claude/conversation_flow_final_summary.md`
- **测试示例**: `tests/conversation_flow/test_orchestrator.py`

## 🎯 下一步

1. **集成到现有API**: 按照上面的示例修改你的API接口
2. **运行集成测试**: `pytest tests/conversation_flow/`
3. **监控生产性能**: 添加Prometheus指标
4. **优化Prompt**: 根据实际效果调整 `prompt_config.py`

---

**需要帮助？** 查看 `README.md` 获取更详细的技术文档。
