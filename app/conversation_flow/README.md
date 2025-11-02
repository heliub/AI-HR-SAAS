# 会话流程编排模块

## 📖 概述

本模块提供候选人AI会话的流程编排功能，采用**高内聚、高并发、高可用、高扩展**的设计原则。

### 核心特性

- ✅ **投机式并行执行**：N1+N2并行、Response组+Question组并行、N4+N9并行，**延迟降低30-50%**
- ✅ **技术异常自动重试**：LLM调用失败自动重试3次，带指数退避
- ✅ **业务异常正常流转**：N5的"答非所问"作为正常流程，不触发重试
- ✅ **可扩展架构**：新增节点只需<30行代码，继承基类即可

---

## 🏗️ 架构设计

### 分层架构

```
┌─────────────────────────────────────────┐
│   FlowOrchestrator (流程编排层)           │
│   - 并行调度                              │
│   - 结果选择                              │
│   - Stage路由                            │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│   NodeExecutor (节点执行层)               │
│   - 单节点执行                            │
│   - LLM调用（CLG1）                       │
│   - 技术异常重试                          │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│   ContextManager (上下文管理层)           │
│   - 会话状态                              │
│   - 模板变量                              │
│   - Stage持久化                          │
└─────────────────────────────────────────┘
```

### 节点分组（高内聚）

#### Group 1: 前置检查组 (Precheck Group)
- **N1**: 转人工意图检测 ✅ **已实现**
- **N2**: 情感分析 ✅ **已实现**
- **特点**: 100%并行，互不依赖

#### Group 2: 问题阶段处理组 (Question Stage Group)
- **N15**: 问题阶段路由 ⏳ 待实现
- **N5**: 回复相关性检查 ⏳ 待实现
- **N6**: 回复满足度检查 ⏳ 待实现
- **N7**: 沟通意愿检查 ⏳ 待实现
- **N14**: 问题状态更新与发送 ⏳ 待实现
- **特点**: 只在Stage2激活，内部有串行依赖

#### Group 3: 对话回复组 (Response Group)
- **N3**: 沟通意愿判断 ⏳ 待实现
- **N4**: 发问检测 ⏳ 待实现
- **N9**: 知识库回复 ⏳ 待实现
- **N10**: 兜底回复 ⏳ 待实现
- **N11**: 闲聊 ⏳ 待实现
- **特点**: Stage1/3常驻，Stage2投机式并行

#### Group 4: 结束语组 (Closing Group)
- **N12**: 高情商结束语 ⏳ 待实现
- **N13**: 复聊语 ⏳ 待实现
- **特点**: 叶子节点，直接返回消息

---

## 🚀 并行执行流程

### 阶段1：前置并行检查

```python
# 并行执行N1和N2
results = await asyncio.gather(
    execute_node_n1(context),  # 转人工检测
    execute_node_n2(context)   # 情感分析
)

# 短路判断（优先级：N1 > N2）
if results[0].action == "SUSPEND":  # 转人工
    return results[0]

if results[1].score == 3:  # 情感极差
    return create_suspend_result()

if results[1].score == 2:  # 情感一般
    return await execute_node_n12(context)  # 高情商结束语

# 情感正常(0/1)，继续阶段2
```

### 阶段2：投机式并行执行

```python
# 读取Stage状态
stage = context.conversation.stage

# 构建并行任务列表
tasks = {
    "response": asyncio.create_task(
        execute_response_group(context)  # N3->N4->N9/N10/N11
    )
}

# Stage2时，投机式并行执行问题组
if stage == "questioning":
    tasks["question"] = asyncio.create_task(
        execute_question_group(context)  # N15->N5/N6/N7->N14
    )

# 等待所有任务完成
results = await asyncio.gather(*tasks.values())

# 结果选择逻辑（见下方）
return select_final_result(stage, results)
```

### 阶段3：结果选择策略

```python
def select_final_result(stage, results):
    """投机式并行的结果选择逻辑"""

    response_result = results["response"]
    question_result = results.get("question")

    # Stage2：问题阶段
    if stage == "questioning":
        # 优先级1：问题组有明确动作
        if question_result and question_result.action != "NONE":
            return question_result

        # 优先级2：对话组中N4判断为"发问" 且 N9有知识库答案
        if (response_result.path == "N3->N4(YES)->N9"
            and response_result.action == "SEND_MESSAGE"):
            return response_result

        # 否则：丢弃对话组结果，使用问题组
        return question_result

    # Stage1/Stage3：直接使用对话组结果
    return response_result
```

---

## 📝 如何实现新节点

### 步骤1：创建节点类

如果节点只需调用一次LLM，继承 `SimpleLLMNode`：

```python
# app/conversation_flow/nodes/response/n3_continue_conversation.py
from typing import Dict, Any
from app.conversation_flow.models import NodeResult, ConversationContext, NodeAction
from app.conversation_flow.nodes.base import SimpleLLMNode


class N3ContinueConversationNode(SimpleLLMNode):
    """N3: 候选人是否愿意沟通"""

    def __init__(self):
        super().__init__(
            node_name="N3",
            scene_name="continue_conversation_with_candidate"
        )

    async def _parse_llm_response(
        self,
        llm_response: Dict[str, Any],
        context: ConversationContext
    ) -> NodeResult:
        """解析LLM响应"""
        willing = llm_response.get("willing", "no").lower()

        if willing == "yes":
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.CONTINUE,
                data={"willing": True}
            )
        else:
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NEXT_NODE,
                next_node=["N12"],  # 跳转到高情商结束语
                data={"willing": False}
            )
```

### 步骤2：创建Prompt模板

在 `app/ai/prompts/conversation_flow/` 目录下创建模板文件：

```markdown
<!-- app/ai/prompts/conversation_flow/continue_conversation_with_candidate.md -->

# 任务
判断候选人是否愿意继续沟通。

## 输入
历史对话：
${历史对话}

## 输出格式
请以JSON格式返回：
{
  "willing": "yes/no",
  "reason": "判断依据"
}

## 判断标准
- 候选人主动提问或表达兴趣 -> "yes"
- 候选人明确拒绝或冷淡回应 -> "no"
```

### 步骤3：注册节点（如需要）

在 `app/conversation_flow/orchestrator.py` 中初始化节点：

```python
class ConversationFlowOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        # ...现有节点

        # 新增节点
        self.n3 = N3ContinueConversationNode()
```

---

## 🔧 复杂节点示例

### 示例1：需要访问数据库的节点（N14）

```python
from app.conversation_flow.nodes.base import NodeExecutor


class N14InformationGatheringNode(NodeExecutor):
    """N14: HR询问的问题处理（无需LLM）"""

    def __init__(self, db: AsyncSession):
        super().__init__(
            node_name="N14",
            scene_name="information_gathering_question",
            db=db
        )

    async def _do_execute(self, context: ConversationContext) -> NodeResult:
        """执行节点（直接操作数据库）"""
        from app.services.conversation_question_tracking_service import (
            ConversationQuestionTrackingService
        )
        from app.services.candidate_conversation_service import (
            CandidateConversationService
        )

        question_service = ConversationQuestionTrackingService(self.db)
        conversation_service = CandidateConversationService(self.db)

        # Step1: 如果是Stage1，初始化问题
        if context.is_greeting_stage:
            # 查询职位设定的问题
            from app.services.job_question_service import JobQuestionService
            job_question_service = JobQuestionService(self.db)

            questions = await job_question_service.get_questions_by_job(
                job_id=context.job_id,
                tenant_id=context.tenant_id
            )

            if not questions:
                # 无问题，直接跳Stage3
                await conversation_service.update_conversation_stage(
                    conversation_id=context.conversation_id,
                    tenant_id=context.tenant_id,
                    stage="intention"
                )
                return NodeResult(
                    node_name=self.node_name,
                    action=NodeAction.NONE
                )

            # 初始化问题到会话
            for question in questions:
                await question_service.create_question_tracking(
                    conversation_id=context.conversation_id,
                    question_id=question.id,
                    job_id=context.job_id,
                    resume_id=context.resume_id,
                    question=question.question,
                    tenant_id=context.tenant_id,
                    user_id=context.user_id,
                    tracking_data={"status": "pending"}
                )

            # 更新Stage为questioning
            await conversation_service.update_conversation_stage(
                conversation_id=context.conversation_id,
                tenant_id=context.tenant_id,
                stage="questioning"
            )

        # Step2: 如果是Stage2，更新当前问题状态
        if context.is_questioning_stage and context.current_question_id:
            await question_service.update_question_status(
                tracking_id=context.current_question_id,
                tenant_id=context.tenant_id,
                status="completed"
            )

        # Step3: 查询下一个要询问的问题
        all_questions = await question_service.get_questions_by_conversation(
            conversation_id=context.conversation_id,
            tenant_id=context.tenant_id
        )

        # 找到第一个pending状态的问题
        next_question = next(
            (q for q in all_questions if q.status == "pending"),
            None
        )

        if not next_question:
            # 没有下一个问题，更新Stage为intention
            await conversation_service.update_conversation_stage(
                conversation_id=context.conversation_id,
                tenant_id=context.tenant_id,
                stage="intention"
            )
            return NodeResult(
                node_name=self.node_name,
                action=NodeAction.NONE
            )

        # 更新问题状态为ongoing
        await question_service.update_question_status(
            tracking_id=next_question.id,
            tenant_id=context.tenant_id,
            status="ongoing"
        )

        return NodeResult(
            node_name=self.node_name,
            action=NodeAction.SEND_MESSAGE,
            message=next_question.question,
            data={"question_id": str(next_question.id)}
        )
```

### 示例2：串行调用多个节点（Response组）

```python
class ResponseGroupExecutor:
    """对话回复组执行器（N3->N4->N9/N10/N11）"""

    def __init__(self, db: AsyncSession):
        self.n3 = N3ContinueConversationNode()
        self.n4 = N4AskQuestionNode()
        self.n9 = N9AnswerBasedOnKnowledgeNode(db)
        self.n10 = N10AnswerWithoutKnowledgeNode()
        self.n11 = N11CasualConversationNode()
        self.n12 = N12HighEQResponseNode()

    async def execute(self, context: ConversationContext) -> NodeResult:
        """执行对话回复链"""

        # 前置条件检查
        if context.is_questioning_stage or context.is_intention_stage:
            # Stage2/3跳过N3
            n3_result = NodeResult(
                node_name="N3",
                action=NodeAction.CONTINUE,
                data={"willing": True}
            )
        else:
            # Stage1执行N3
            n3_result = await self.n3.execute(context)

        # N3不愿意沟通 -> N12结束语
        if not n3_result.data.get("willing"):
            return await self.n12.execute(context)

        # 并行执行N4和N9（投机式优化）
        n4_task = asyncio.create_task(self.n4.execute(context))
        n9_task = asyncio.create_task(self.n9.execute(context))

        n4_result, n9_result = await asyncio.gather(n4_task, n9_task)

        # N4判断候选人是否发问
        if n4_result.data.get("is_question"):
            # 使用N9结果
            if n9_result.action == NodeAction.SEND_MESSAGE:
                return n9_result
            else:
                # 知识库无答案，使用N10
                return await self.n10.execute(context)
        else:
            # 未发问，执行N11闲聊
            return await self.n11.execute(context)
```

---

## 📊 性能分析

### 投机式并行的收益

| 场景 | 串行耗时 | 并行耗时 | 收益 |
|-----|---------|---------|-----|
| Stage1 | N1(1s) + N2(1s) + N3(1s) + N4(1s) + N9(2s) = 6s | max(N1,N2) + max(N4,N9) = 1s + 2s = 3s | **50%** |
| Stage2(候选人发问) | N1(1s) + N2(1s) + N15(0.5s) + N5(1s) + N3(1s) + N4(1s) + N9(2s) = 7.5s | max(N1,N2) + max(Question组, Response组) = 1s + max(2.5s, 4s) = 5s | **33%** |
| Stage2(正常回答) | N1(1s) + N2(1s) + N15(0.5s) + N5(1s) + N14(0.5s) = 4s | max(N1,N2) + Question组 = 1s + 2s = 3s | **25%** |

---

## 🧪 测试示例

```python
# tests/conversation_flow/test_orchestrator.py
import pytest
from app.conversation_flow import (
    ConversationFlowOrchestrator,
    ConversationContext,
    ConversationStage,
    ConversationStatus,
    PositionInfo,
    NodeAction
)


@pytest.mark.asyncio
async def test_precheck_phase_transfer_human(db_session):
    """测试：候选人申请转人工"""
    orchestrator = ConversationFlowOrchestrator(db=db_session)

    context = ConversationContext(
        conversation_id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        job_id=uuid4(),
        resume_id=uuid4(),
        conversation_status=ConversationStatus.ONGOING,
        conversation_stage=ConversationStage.GREETING,
        last_candidate_message="我想和真人HR沟通",
        history=[],
        position_info=PositionInfo(id=uuid4(), name="Python工程师")
    )

    result = await orchestrator.execute(context)

    assert result.action == NodeAction.SUSPEND
    assert "转人工" in result.reason


@pytest.mark.asyncio
async def test_precheck_phase_bad_emotion(db_session):
    """测试：候选人情感极差"""
    orchestrator = ConversationFlowOrchestrator(db=db_session)

    context = ConversationContext(
        conversation_id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        job_id=uuid4(),
        resume_id=uuid4(),
        conversation_status=ConversationStatus.ONGOING,
        conversation_stage=ConversationStage.GREETING,
        last_candidate_message="你们公司太垃圾了！",
        history=[],
        position_info=PositionInfo(id=uuid4(), name="Python工程师")
    )

    result = await orchestrator.execute(context)

    assert result.action == NodeAction.SUSPEND
    assert "情感" in result.reason
```

---

## 📚 下一步工作

### 待实现节点清单

- [ ] N3: 沟通意愿判断
- [ ] N4: 发问检测
- [ ] N5: 回复相关性检查
- [ ] N6: 回复满足度检查
- [ ] N7: 沟通意愿检查
- [ ] N9: 知识库回复
- [ ] N10: 兜底回复
- [ ] N11: 闲聊
- [ ] N12: 高情商结束语
- [ ] N13: 复聊语
- [ ] N14: 问题状态更新
- [ ] N15: 问题阶段路由

### 待实现组件

- [ ] ResponseGroupExecutor
- [ ] QuestionGroupExecutor
- [ ] 完善Orchestrator的并行执行逻辑

### Prompt模板清单

需要在 `app/ai/prompts/conversation_flow/` 目录下创建以下模板文件：

- `transfer_human_intent.md` ✅
- `candidate_emotion.md` ✅
- `continue_conversation_with_candidate.md`
- `candidate_ask_question.md`
- `relevance_reply_and_question.md`
- `reply_match_question_requirement.md`
- `candidate_communication_willingness_for_question.md`
- `candidate_position_willingness.md`
- `answer_based_on_knowledge.md`
- `answer_without_knowledge.md`
- `casual_conversation.md`
- `high_eq_response.md`
- `resume_conversation.md`

---

## 🤝 贡献指南

1. 参考 `N1TransferHumanIntentNode` 和 `N2EmotionAnalysisNode` 的实现
2. 继承 `SimpleLLMNode` 或 `NodeExecutor`
3. 实现 `_parse_llm_response` 或 `_do_execute` 方法
4. 创建对应的Prompt模板文件
5. 在Orchestrator中注册节点
6. 编写单元测试

---

## 📞 联系方式

如有问题，请查阅：
- 架构文档：[CLAUDE.md](/CLAUDE.md)
- API文档：[COMPLETE_API_REFERENCE.md](/docs/COMPLETE_API_REFERENCE.md)
- 对话流程：[candidate_chat_flow.md](/docs/candidate_chat_flow.md)
