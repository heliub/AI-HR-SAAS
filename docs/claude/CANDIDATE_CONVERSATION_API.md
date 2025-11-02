# 候选人会话API文档

## 概述

候选人会话API提供了前端与候选人进行对话的接口，支持：
1. 查询会话消息列表
2. 候选人发送消息并获取AI自动回复
3. 查询会话详情

所有API都会自动执行对话流程（ConversationFlowOrchestrator），包括：
- 前置检查（转人工意图、情感分析）
- 智能回复（知识库搜索、问题回答、闲聊）
- 阶段管理（Stage1开场、Stage2问题、Stage3意向）

---

## API端点

### 1. 获取会话消息列表

**接口地址**: `GET /api/v1/candidate-conversations/{conversation_id}/messages`

**描述**: 根据会话ID获取该会话的所有消息记录，支持分页。

**请求参数**:

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| conversation_id | UUID | Path | 是 | 会话ID |
| limit | int | Query | 否 | 返回消息数量（默认100，最大500） |
| offset | int | Query | 否 | 偏移量（默认0，用于分页） |

**请求示例**:
```http
GET /api/v1/candidate-conversations/123e4567-e89b-12d3-a456-426614174000/messages?limit=50&offset=0
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "total": 128,
  "messages": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "conversationId": "123e4567-e89b-12d3-a456-426614174000",
      "sender": "ai",
      "message": "您好！感谢您关注我们的Python工程师职位。",
      "messageType": "greeting",
      "createdAt": "2025-11-02T10:00:00Z",
      "updatedAt": "2025-11-02T10:00:00Z"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "conversationId": "123e4567-e89b-12d3-a456-426614174000",
      "sender": "candidate",
      "message": "你好，我想了解一下这个职位的薪资范围",
      "messageType": "text",
      "createdAt": "2025-11-02T10:01:00Z",
      "updatedAt": "2025-11-02T10:01:00Z"
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "conversationId": "123e4567-e89b-12d3-a456-426614174000",
      "sender": "ai",
      "message": "根据职位信息，薪资范围是15-25K，具体根据您的经验和能力确定。",
      "messageType": "answer",
      "createdAt": "2025-11-02T10:01:02Z",
      "updatedAt": "2025-11-02T10:01:02Z"
    }
  ]
}
```

**错误响应**:
```json
{
  "detail": "会话不存在或无权限访问"
}
```
HTTP状态码: 404

---

### 2. 候选人发送消息

**接口地址**: `POST /api/v1/candidate-conversations/{conversation_id}/messages`

**描述**: 候选人发送消息，系统自动执行对话流程并返回AI回复。

**请求参数**:

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| conversation_id | UUID | Path | 是 | 会话ID |
| content | string | Body | 是 | 消息内容（1-2000字符） |

**请求示例**:
```http
POST /api/v1/candidate-conversations/123e4567-e89b-12d3-a456-426614174000/messages
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "请问这个职位的工作地点在哪里？"
}
```

**响应示例**:

**场景1：正常对话（AI回复）**
```json
{
  "candidateMessage": {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "conversationId": "123e4567-e89b-12d3-a456-426614174000",
    "sender": "candidate",
    "content": "请问这个职位的工作地点在哪里？",
    "messageType": "text",
    "createdAt": "2025-11-02T10:02:00Z",
    "updatedAt": "2025-11-02T10:02:00Z"
  },
  "aiMessage": {
    "id": "990e8400-e29b-41d4-a716-446655440004",
    "conversationId": "123e4567-e89b-12d3-a456-426614174000",
    "sender": "ai",
    "content": "工作地点在北京朝阳区，交通便利，地铁直达。",
    "messageType": "answer",
    "createdAt": "2025-11-02T10:02:01Z",
    "updatedAt": "2025-11-02T10:02:01Z"
  },
  "action": "send_message",
  "conversationStatus": "ongoing",
  "conversationStage": "greeting"
}
```

**场景2：转人工（候选人明确要求）**
```json
{
  "candidateMessage": {
    "id": "aa0e8400-e29b-41d4-a716-446655440005",
    "conversationId": "123e4567-e89b-12d3-a456-426614174000",
    "sender": "candidate",
    "content": "我想直接和HR聊",
    "messageType": "text",
    "createdAt": "2025-11-02T10:03:00Z",
    "updatedAt": "2025-11-02T10:03:00Z"
  },
  "aiMessage": {
    "id": "bb0e8400-e29b-41d4-a716-446655440006",
    "conversationId": "123e4567-e89b-12d3-a456-426614174000",
    "sender": "ai",
    "content": "好的，我已经为您转接人工客服，HR会尽快与您联系。",
    "messageType": "answer",
    "createdAt": "2025-11-02T10:03:01Z",
    "updatedAt": "2025-11-02T10:03:01Z"
  },
  "action": "suspend",
  "conversationStatus": "interrupted",
  "conversationStage": "greeting"
}
```

**错误响应**:

1. 会话不存在
```json
{
  "detail": "会话不存在或无权限访问"
}
```
HTTP状态码: 404

2. 会话已结束
```json
{
  "detail": "会话已ended，无法继续对话"
}
```
HTTP状态码: 400

---

### 3. 获取会话详情

**接口地址**: `GET /api/v1/candidate-conversations/{conversation_id}`

**描述**: 获取会话详情，包含基本信息和最新10条消息。

**请求参数**:

| 参数名 | 类型 | 位置 | 必填 | 说明 |
|--------|------|------|------|------|
| conversation_id | UUID | Path | 是 | 会话ID |

**请求示例**:
```http
GET /api/v1/candidate-conversations/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "tenantId": "tenant-uuid",
  "userId": "user-uuid",
  "resumeId": "resume-uuid",
  "jobId": "job-uuid",
  "status": "ongoing",
  "stage": "greeting",
  "summary": null,
  "latestMessages": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "conversationId": "123e4567-e89b-12d3-a456-426614174000",
      "sender": "ai",
      "message": "您好！感谢您关注我们的Python工程师职位。",
      "messageType": "greeting",
      "createdAt": "2025-11-02T10:00:00Z",
      "updatedAt": "2025-11-02T10:00:00Z"
    }
    // ... 最多10条消息
  ],
  "messageCount": 15,
  "createdAt": "2025-11-02T09:58:00Z",
  "updatedAt": "2025-11-02T10:03:01Z"
}
```

**错误响应**:
```json
{
  "detail": "会话不存在或无权限访问"
}
```
HTTP状态码: 404

---

## 数据模型

### ConversationMessage（消息）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 消息ID |
| conversationId | UUID | 会话ID（可选，兼容旧数据） |
| resumeId | UUID | 简历ID |
| sender | string | 发送者：candidate/ai |
| message | string | 消息内容 |
| messageType | string | 消息类型：text/greeting/question/answer/closing |
| metadata | object | 元数据（节点信息、执行路径等） |
| createdAt | datetime | 创建时间 |
| updatedAt | datetime | 更新时间 |

### Sender枚举

- **candidate**: 候选人发送的消息
- **ai**: AI助手回复的消息
- **system**: 系统消息（如阶段转换提示）

### MessageType枚举

- **text**: 普通文本
- **greeting**: 开场白
- **question**: 问题
- **answer**: 回答
- **closing**: 结束语

### Action枚举

- **send_message**: 发送消息（正常对话）
- **suspend**: 转人工
- **none**: 无动作（如Stage转换）

### ConversationStatus枚举

- **opened**: 会话已开启（刚创建）
- **ongoing**: 沟通中
- **interrupted**: 已中断（转人工）
- **ended**: 会话结束
- **deleted**: 已删除

### ConversationStage枚举

- **greeting**: Stage1 - 开场白阶段
- **questioning**: Stage2 - 问题询问阶段
- **intention**: Stage3 - 职位意向询问阶段
- **matched**: 撮合成功

---

## 对话流程说明

### 执行流程

当候选人发送消息时，系统会自动执行以下流程：

```
候选人消息
  ↓
保存到数据库
  ↓
加载历史消息（最近50条）
  ↓
构建ConversationContext
  ↓
执行ConversationFlowOrchestrator
  ├─ 阶段1：前置并行检查
  │   ├─ N1: 转人工意图检测
  │   └─ N2: 情感分析
  ├─ 短路判断
  │   ├─ 转人工 → 返回suspend
  │   └─ 情感极差 → 发送高情商结束语
  └─ 阶段2：投机式并行执行
      ├─ Response组（N3-N10）
      │   ├─ N3: 继续沟通意愿
      │   ├─ N4+N9并行: 发问检测+知识库搜索
      │   └─ N10: 兜底回复
      └─ Question组（N14-N15，仅Stage2）
          ├─ N14: 问题初始化
          └─ N15: 问题路由
  ↓
保存AI回复到数据库
  ↓
更新会话状态
  ↓
返回响应
```

### 性能优化

- **并行执行**: N1+N2并行、N4+N9并行、Response组+Question组并行
- **预期性能**: 平均响应时间 < 3秒
- **降级策略**: LLM失败时自动降级，避免转人工

---

## 前端集成示例

### Vue 3 + TypeScript

```typescript
// services/conversationApi.ts
import axios from 'axios'

interface SendMessageRequest {
  content: string
}

interface SendMessageResponse {
  candidateMessage: Message
  aiMessage: Message | null
  action: 'send_message' | 'suspend' | 'none'
  conversationStatus: string
  conversationStage: string
}

interface Message {
  id: string
  conversationId: string
  sender: 'candidate' | 'ai' | 'system'
  content: string
  messageType: string
  metadata: any
  createdAt: string
  updatedAt: string
}

export const conversationApi = {
  // 获取消息列表
  async getMessages(conversationId: string, limit = 100, offset = 0) {
    const response = await axios.get(
      `/api/v1/candidate-conversations/${conversationId}/messages`,
      { params: { limit, offset } }
    )
    return response.data
  },

  // 发送消息
  async sendMessage(conversationId: string, content: string): Promise<SendMessageResponse> {
    const response = await axios.post(
      `/api/v1/candidate-conversations/${conversationId}/messages`,
      { content }
    )
    return response.data
  },

  // 获取会话详情
  async getConversationDetail(conversationId: string) {
    const response = await axios.get(
      `/api/v1/candidate-conversations/${conversationId}`
    )
    return response.data
  }
}
```

### React Hook示例

```typescript
// hooks/useConversation.ts
import { useState, useCallback } from 'react'
import { conversationApi } from '@/services/conversationApi'

export const useConversation = (conversationId: string) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)

  // 加载消息
  const loadMessages = useCallback(async () => {
    setLoading(true)
    try {
      const data = await conversationApi.getMessages(conversationId)
      setMessages(data.messages)
    } catch (error) {
      console.error('加载消息失败', error)
    } finally {
      setLoading(false)
    }
  }, [conversationId])

  // 发送消息
  const sendMessage = useCallback(async (content: string) => {
    setSending(true)
    try {
      const response = await conversationApi.sendMessage(conversationId, content)

      // 添加候选人消息
      setMessages(prev => [...prev, response.candidateMessage])

      // 添加AI回复（如果有）
      if (response.aiMessage) {
        setMessages(prev => [...prev, response.aiMessage!])
      }

      // 处理转人工场景
      if (response.action === 'suspend') {
        alert('已转接人工客服')
      }

      return response
    } catch (error) {
      console.error('发送消息失败', error)
      throw error
    } finally {
      setSending(false)
    }
  }, [conversationId])

  return {
    messages,
    loading,
    sending,
    loadMessages,
    sendMessage
  }
}
```

---

## 注意事项

1. **权限控制**: 所有API都需要Bearer Token认证
2. **租户隔离**: 自动根据当前用户的tenant_id过滤数据
3. **消息持久化**: 所有消息都会保存到数据库，支持历史回溯
4. **会话状态**: 转人工后会话状态变为`interrupted`，无法继续对话
5. **性能**: 使用了并行执行优化，平均响应时间 < 3秒
6. **降级策略**: LLM失败时会自动降级，不会直接报错

---

## 数据库迁移

请执行以下SQL创建消息表：

```sql
-- 见 CONVERSATION_MESSAGES_MIGRATION.sql
```

---

## 测试建议

### 测试场景

1. **正常对话**: 候选人询问职位信息，AI从知识库回答
2. **转人工**: 候选人说"我想和HR聊"，触发转人工
3. **情感检测**: 候选人表达不满，触发高情商结束语
4. **问题阶段**: Stage2时，AI按顺序提问
5. **并发安全**: 多个候选人同时发消息，验证无冲突

### Postman测试集

```json
{
  "info": {
    "name": "候选人会话API测试"
  },
  "item": [
    {
      "name": "获取消息列表",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/v1/candidate-conversations/{{conversation_id}}/messages"
      }
    },
    {
      "name": "发送普通消息",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/v1/candidate-conversations/{{conversation_id}}/messages",
        "body": {
          "mode": "raw",
          "raw": "{\"content\": \"请问薪资范围是多少？\"}"
        }
      }
    },
    {
      "name": "触发转人工",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/v1/candidate-conversations/{{conversation_id}}/messages",
        "body": {
          "mode": "raw",
          "raw": "{\"content\": \"我想和HR直接聊\"}"
        }
      }
    }
  ]
}
```
