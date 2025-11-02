# 候选人对话流程优化方案

## 概述

本文档描述了候选人对话流程的优化方案，主要通过节点组合和并行执行来提高响应效率。

## 节点定义

根据原始文档，候选人对话流程包含以下节点：

- N1：候选人是否申请转人工
- N2：候选人情感分析
- N3：候选人是否愿意沟通
- N4：候选人是否发问
- N5：候选人回复和问题相关性
- N6：候选人的回复是否满足设定的要求
- N7：候选人针对问题的沟通意愿
- N8：候选人对职位是否有意向
- N9：基于知识库回复求职者
- N10：无知识库时兜底回复
- N11：陪候选人闲聊
- N12：高情商回复（结束语）
- N13：复聊语
- N14：HR询问的问题处理
- N15：问题询问阶段处理

## 节点组合方案

为了提高响应效率，我们将细分的节点组合成多个大节点：

### CombineNode1: 前置过滤判断

- **组合节点**: N1(转人工判断) + N2(情感分析)
- **执行逻辑**: 并行执行N1和N2，因为这两个节点互不依赖，可以同时执行
- **输出结果**: 
  - 如果N1结果为转人工，则直接返回SUSPEND
  - 否则根据N2的情感分数决定下一步流程

### CombineNode2: 问题阶段处理逻辑

- **组合节点**: N5(回复相关性) + N6(回复满足要求) + N7(沟通意愿) + N14(问题处理)
- **执行逻辑**: 
  - 首先执行N14判断当前阶段和问题类型
  - 根据N14的结果，选择性执行N5、N6或N7
  - 最后执行N14的问题处理逻辑

### CombineNode3: 消息回复方法

- **组合节点**: N3(沟通意愿) + N4(是否发问) + N9(知识库回复) + N10(兜底回复) + N11(闲聊)
- **执行逻辑**: 
  - 首先执行N3判断沟通意愿
  - 如果愿意沟通，执行N4判断是否发问
  - 根据N4结果，选择执行N9/N10或N11

## 并行执行设计

### 阶段1: 并行前置判断

```python
async def parallel_pre_filter(conversation_id, message):
    # 并行执行N1和N2
    task1 = asyncio.create_task(execute_node_N1(conversation_id, message))
    task2 = asyncio.create_task(execute_node_N2(conversation_id, message))
    
    # 等待两个任务完成
    n1_result, n2_result = await asyncio.gather(task1, task2)
    
    # 处理结果
    if n1_result.action == "SUSPEND":
        return n1_result
    
    return n2_result
```

### 阶段2: 条件并行执行

根据会话阶段和前置过滤结果，选择性地并行执行相关节点：

```python
async def conditional_parallel_execution(conversation_id, message, stage):
    if stage == "questioning":
        # 问题询问阶段的并行处理
        return await execute_questioning_stage(conversation_id, message)
    elif stage == "greeting":
        # 开场白阶段的并行处理
        return await execute_greeting_stage(conversation_id, message)
    elif stage == "intention":
        # 职位意向询问阶段
        return await execute_intention_stage(conversation_id, message)
```

## 整体流程设计

```python
async def process_candidate_message(conversation_id, candidate_message):
    # 1. 保存候选人消息
    await save_candidate_message(conversation_id, candidate_message)
    
    # 2. 获取会话信息
    conversation = await get_conversation(conversation_id)
    
    # 3. 并行执行前置过滤 (CombineNode1)
    pre_filter_result = await parallel_pre_filter(conversation_id, candidate_message)
    
    # 4. 处理前置过滤结果
    if pre_filter_result.action == "SUSPEND":
        return pre_filter_result
    
    # 5. 根据会话阶段执行不同逻辑
    if conversation.stage == "questioning":
        result = await execute_questioning_stage(conversation_id, candidate_message)
    elif conversation.stage == "greeting":
        result = await execute_greeting_stage(conversation_id, candidate_message)
    elif conversation.stage == "intention":
        result = await execute_intention_stage(conversation_id, candidate_message)
    
    # 6. 保存AI回复并返回
    if result.action == "SEND_MESSAGE":
        await save_ai_message(conversation_id, result.message)
    
    return result
```

## 性能优化效果

通过节点组合和并行执行，我们可以实现以下性能优化：

1. **减少串行执行时间**: 将原本需要串行执行的N1和N2节点并行执行，减少约50%的执行时间。
2. **智能节点选择**: 根据会话阶段和前置过滤结果，只执行必要的节点，避免不必要的计算。
3. **批量处理**: 将相关的节点组合在一起，减少数据库访问次数和LLM调用次数。

## 实现细节

### 1. 异步任务管理

使用Python的asyncio库管理并行任务：

```python
# 创建并行任务
tasks = [
    asyncio.create_task(execute_node_n1(conversation_id, message)),
    asyncio.create_task(execute_node_n2(conversation_id, message))
]

# 等待所有任务完成
results = await asyncio.gather(*tasks)
```

### 2. 错误处理

为每个节点添加错误处理，确保单个节点的失败不会影响整个流程：

```python
async def execute_node_with_error_handling(node_func, *args, **kwargs):
    try:
        return await node_func(*args, **kwargs)
    except Exception as e:
        # 记录错误日志
        logger.error(f"Node execution failed: {str(e)}")
        # 返回默认结果
        return get_default_result_for_node(node_func.__name__)
```

### 3. 超时控制

为每个节点设置超时时间，防止长时间阻塞：

```python
async def execute_node_with_timeout(node_func, timeout=5.0, *args, **kwargs):
    try:
        return await asyncio.wait_for(node_func(*args, **kwargs), timeout=timeout)
    except asyncio.TimeoutError:
        # 处理超时情况
        return get_timeout_result_for_node(node_func.__name__)
```

## API设计

### 1. 消息处理接口

```python
POST /api/v1/candidate-conversations/{conversation_id}/messages
{
    "message": "候选人消息内容"
}
```

### 2. 响应格式

```json
{
    "code": 200,
    "message": "消息处理成功",
    "data": {
        "action": "SEND_MESSAGE",
        "message": "AI回复内容",
        "messageType": "text",
        "conversationId": "会话ID",
        "stage": "当前会话阶段"
    }
}
```

## 总结

通过节点组合和并行执行，候选人对话流程的响应时间可以显著提高，同时保持流程的完整性和准确性。这种优化方案不仅提高了用户体验，还减少了系统资源的消耗。

## 后续优化方向

1. **缓存优化**: 对频繁访问的数据进行缓存，如会话信息、职位信息等。
2. **LLM调用优化**: 批量处理多个LLM请求，减少网络开销。
3. **智能预测**: 基于历史数据预测下一步可能执行的节点，提前准备相关资源。
4. **负载均衡**: 将不同类型的节点分配到不同的服务器上，实现负载均衡。
