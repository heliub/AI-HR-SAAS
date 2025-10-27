# AI HR SaaS 系统 - 完整API接口文档

## 📋 目录

- [系统概述](#系统概述)
- [认证说明](#认证说明)
- [用户管理](#用户管理)
- [职位管理](#职位管理)
- [简历管理](#简历管理)
- [渠道管理](#渠道管理)
- [任务管理](#任务管理)
- [面试管理](#面试管理)
- [统计数据](#统计数据)
- [错误处理](#错误处理)

---

## 系统概述

AI HR SaaS 系统是一套智能化人力资源管理平台，提供简历分析、AI匹配、招聘管理等功能。

**基础URL**: `http://localhost:8000/api/v1`

**数据格式**: JSON

**字符编码**: UTF-8

**API版本**: v1

---

## 认证说明

### 🔐 认证方式

系统使用 Bearer Token 认证，所有需要认证的接口都需要在请求头中添加：

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

### 👥 用户角色与权限

| 角色 | 权限描述 | 可访问数据 |
|------|----------|------------|
| `admin` | 租户管理员 | 租户内所有业务数据（除chat_sessions） |
| `hr` | 人力资源专员 | 只能查看自己负责的数据 |

### 🚪 认证接口

#### 用户登录
**POST** `/auth/login`

**请求体**:
```json
{
  "email": "li@demo.com",
  "password": "your-password"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "10000000-0000-0000-0000-000000000004",
      "name": "李技术总监",
      "email": "li@demo.com",
      "role": "admin",
      "tenant_id": "00000000-0000-0000-0000-000000000001",
      "avatar_url": null,
      "last_login_at": "2025-01-27T10:30:00Z",
      "is_active": true
    }
  }
}
```

---

## 用户管理

### 👤 获取当前用户信息

**GET** `/account/profile`

获取当前登录用户的详细信息

**响应**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": "10000000-0000-0000-0000-000000000004",
    "name": "李技术总监",
    "email": "li@demo.com",
    "role": "admin",
    "tenant_id": "00000000-0000-0000-0000-000000000001",
    "avatar_url": null,
    "last_login_at": "2025-01-27T10:30:00Z",
    "is_active": true,
    "created_at": "2025-01-27T10:30:00Z",
    "updated_at": "2025-01-27T10:30:00Z"
  }
}
```

### ✏️ 更新用户信息

**PUT** `/account/profile`

更新当前用户信息

**请求体**:
```json
{
  "name": "新用户名",
  "avatar_url": "https://example.com/new-avatar.jpg"
}
```

---

## 职位管理

### 📋 获取职位列表

**GET** `/jobs`

获取职位列表，管理员可查看所有职位，HR只能查看自己创建的职位

**查询参数**:
- `page` (int, optional): 页码，默认1，最小值1
- `pageSize` (int, optional): 每页数量，默认10，范围1-100
- `search` (string, optional): 搜索关键词（标题、部门、描述）
- `status` (string, optional): 职位状态筛选
- `department` (string, optional): 部门筛选

**请求示例**:
```http
GET /api/v1/jobs?page=1&pageSize=10&search=前端&status=open
Authorization: Bearer YOUR_TOKEN
```

**响应**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "total": 25,
    "page": 1,
    "pageSize": 10,
    "list": [
      {
        "id": "30000000-0000-0000-0000-000000000001",
        "title": "高级前端工程师",
        "department": "技术部",
        "location": "北京",
        "type": "full-time",
        "status": "open",
        "minSalary": 25000,
        "maxSalary": 45000,
        "salary": "25K-45K",
        "description": "负责公司核心产品的前端开发工作...",
        "requirements": ["React", "TypeScript", "5年以上经验"],
        "recruitmentInvitation": "我们正在寻找优秀的前端工程师加入团队...",
        "education": "本科及以上",
        "minAge": 22,
        "maxAge": 40,
        "jobLevel": "P6-P7",
        "applicantsCount": 15,
        "userId": "10000000-0000-0000-0000-000000000004",
        "createdBy": "10000000-0000-0000-0000-000000000004",
        "publishedAt": "2025-01-27T10:30:00Z",
        "createdAt": "2025-01-27T10:30:00Z",
        "updatedAt": "2025-01-27T10:30:00Z"
      }
    ]
  }
}
```

### 🔍 获取职位详情

**GET** `/jobs/{job_id}`

获取指定职位的详细信息

**路径参数**:
- `job_id` (UUID): 职位ID

**响应**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "id": "30000000-0000-0000-0000-000000000001",
    "title": "高级前端工程师",
    "department": "技术部",
    "location": "北京",
    "type": "full-time",
    "status": "open",
    "minSalary": 25000,
    "maxSalary": 45000,
    "salary": "25K-45K",
    "description": "负责公司核心产品的前端开发工作，参与产品需求分析和技术方案设计...",
    "requirements": ["React", "TypeScript", "5年以上经验", "大厂背景优先"],
    "recruitmentInvitation": "我们正在寻找优秀的前端工程师加入我们的技术团队！你将有机会参与创新项目...",
    "education": "本科及以上",
    "minAge": 22,
    "maxAge": 40,
    "jobLevel": "P6-P7",
    "applicantsCount": 15,
    "userId": "10000000-0000-0000-0000-000000000004",
    "createdBy": "10000000-0000-0000-0000-000000000004",
    "publishedAt": "2025-01-27T10:30:00Z",
    "createdAt": "2025-01-27T10:30:00Z",
    "updatedAt": "2025-01-27T10:30:00Z"
  }
}
```

### ➕ 创建职位

**POST** `/jobs`

创建新职位（自动设置当前用户为创建者）

**请求体**:
```json
{
  "title": "高级后端工程师",
  "department": "技术部",
  "location": "北京",
  "type": "full-time",
  "minSalary": 30000,
  "maxSalary": 50000,
  "description": "负责后端服务开发和架构设计...",
  "requirements": ["Java", "Spring Boot", "微服务"],
  "recruitmentInvitation": "寻找优秀的后端工程师...",
  "education": "本科及以上",
  "minAge": 25,
  "maxAge": 45,
  "jobLevel": "P7-P8"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "职位创建成功",
  "data": {
    "id": "30000000-0000-0000-0000-000000000002",
    "title": "高级后端工程师",
    "department": "技术部",
    "status": "draft",
    "createdAt": "2025-01-27T11:00:00Z",
    "userId": "10000000-0000-0000-0000-000000000004",
    "createdBy": "10000000-0000-0000-0000-000000000004"
  }
}
```

### ✏️ 更新职位

**PUT** `/jobs/{job_id}`

更新指定职位信息（只有职位创建者或管理员可以更新）

**请求体**:
```json
{
  "title": "更新的职位名称",
  "status": "closed",
  "description": "更新的职位描述...",
  "minSalary": 28000,
  "maxSalary": 48000
}
```

### 🗑️ 删除职位

**DELETE** `/jobs/{job_id}`

删除指定职位（只有职位创建者或管理员可以删除）

**响应**:
```json
{
  "code": 200,
  "message": "职位删除成功"
}
```

### 📊 更新职位状态

**PATCH** `/jobs/{job_id}/status`

更新职位状态

**请求体**:
```json
{
  "status": "open|closed|draft"
}
```

### 📋 复制职位

**POST** `/jobs/{job_id}/duplicate`

复制现有职位创建新职位

**响应**:
```json
{
  "code": 200,
  "message": "职位复制成功",
  "data": {
    "id": "30000000-0000-0000-0000-000000000003",
    "title": "高级前端工程师 (副本)",
    "createdAt": "2025-01-27T11:30:00Z"
  }
}
```

### 🤖 AI生成职位描述

**POST** `/jobs/ai-generate`

AI智能生成职位描述和要求

**请求体**:
```json
{
  "title": "高级前端工程师",
  "description": "负责前端开发和性能优化"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "生成成功",
  "data": {
    "department": "技术部",
    "location": "北京/上海/深圳",
    "minSalary": 20000,
    "maxSalary": 45000,
    "description": "1. 负责公司高级前端工程师相关的开发工作，参与产品需求分析和技术方案设计\n2. 编写高质量、可维护的代码，完成核心功能模块开发...",
    "requirements": ["• 3年以上相关开发经验，有大型项目经验者优先", "• 熟练掌握相关技术栈和开发工具"],
    "recruitmentInvitation": "我们正在寻找优秀的高级前端工程师加入我们的技术团队！你将有机会参与创新项目...",
    "education": "本科及以上",
    "minAge": 22,
    "maxAge": 45
  }
}
```

---

## 简历管理

### 📄 获取简历列表

**GET** `/resumes`

获取简历列表，管理员可查看所有简历，HR只能查看自己负责的简历

**查询参数**:
- `page` (int, optional): 页码，默认1，最小值1
- `pageSize` (int, optional): 每页数量，默认10，范围1-100
- `search` (string, optional): 搜索关键词（姓名、邮箱、职位）
- `status` (string, optional): 简历状态筛选
- `jobId` (UUID, optional): 职位ID筛选

**响应**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "total": 50,
    "page": 1,
    "pageSize": 10,
    "list": [
      {
        "id": "40000000-0000-0000-0000-000000000001",
        "candidateName": "张伟",
        "email": "zhangwei@example.com",
        "phone": "13800138000",
        "position": "高级前端工程师",
        "status": "pending",
        "source": "智联招聘",
        "experienceYears": "6年",
        "educationLevel": "本科",
        "age": 29,
        "gender": "male",
        "location": "北京",
        "school": "北京大学",
        "major": "计算机科学与技术",
        "skills": ["React", "TypeScript", "Node.js", "Next.js"],
        "submittedAt": "2025-01-13T10:30:00Z",
        "conversationSummary": "候选人张伟在字节跳动有丰富的前端开发经验...",
        "userId": "10000000-0000-0000-0000-000000000002",
        "createdAt": "2025-01-27T10:30:00Z",
        "updatedAt": "2025-01-27T10:30:00Z"
      }
    ]
  }
}
```

### 📄 获取简历详情

**GET** `/resumes/{resume_id}`

获取指定简历的完整详细信息（包含所有关联数据）

**路径参数**:
- `resume_id` (UUID): 简历ID

**响应**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "id": "40000000-0000-0000-0000-000000000001",
    "candidateName": "张伟",
    "email": "zhangwei@example.com",
    "phone": "13800138000",
    "position": "高级前端工程师",
    "status": "pending",
    "source": "智联招聘",
    "experienceYears": "6年",
    "educationLevel": "本科",
    "age": 29,
    "gender": "male",
    "location": "北京",
    "school": "北京大学",
    "major": "计算机科学与技术",
    "skills": ["React", "TypeScript", "Node.js", "Next.js"],
    "submittedAt": "2025-01-13T10:30:00Z",
    "conversationSummary": "候选人张伟在字节跳动有丰富的前端开发经验，主导开发了抖音创作者平台...",
    "userId": "10000000-0000-0000-0000-000000000002",

    // 工作经历
    "workHistory": [
      {
        "id": "41000000-0000-0000-0000-000000000001",
        "company": "字节跳动",
        "position": "高级前端工程师",
        "startDate": "2021-03",
        "endDate": "至今",
        "description": "负责抖音创作者平台的前端开发，从0到1搭建整个平台，目前支持百万级创作者使用"
      },
      {
        "id": "41000000-0000-0000-0000-000000000002",
        "company": "美团",
        "position": "前端工程师",
        "startDate": "2019-07",
        "endDate": "2021-02",
        "description": "参与美团外卖平台重构，优化页面性能，提升用户体验"
      }
    ],

    // 项目经历
    "projectHistory": [
      {
        "id": "42000000-0000-0000-0000-000000000001",
        "name": "抖音创作者平台",
        "role": "前端负责人",
        "startDate": "2021-03",
        "endDate": "至今",
        "description": "从0到1搭建创作者平台，支持百万级创作者使用，包括内容发布、数据分析、变现等功能",
        "technologies": ["React", "TypeScript", "Next.js", "Node.js", "GraphQL"]
      }
    ],

    // 教育背景
    "educationHistory": [
      {
        "id": "43000000-0000-0000-0000-000000000001",
        "school": "北京大学",
        "degree": "本科",
        "major": "计算机科学与技术",
        "startDate": "2015-09",
        "endDate": "2019-06"
      }
    ],

    // 求职意向
    "jobPreferences": {
      "id": "44000000-0000-0000-0000-000000000001",
      "expectedSalary": "35K-45K",
      "preferredLocations": ["北京", "上海"],
      "jobType": "full-time",
      "availableDate": "2025-02-01"
    },

    // AI匹配结果
    "aiMatchResults": [
      {
        "id": "45000000-0000-0000-0000-000000000001",
        "isMatch": true,
        "score": 92,
        "reason": "候选人具备丰富的前端开发经验，技术栈完全匹配（React/TypeScript/Next.js），有大厂背景，项目经验丰富。在性能优化方面有深入实践，成功将页面加载时间从3s优化到1s以内。",
        "strengths": ["技术栈匹配", "大厂背景", "项目经验丰富", "性能优化经验"],
        "weaknesses": ["薪资期望略高于预算"],
        "recommendation": "强烈推荐安排技术面试"
      }
    ],

    // 聊天记录
    "chatHistory": [
      {
        "id": "46000000-0000-0000-0000-000000000001",
        "sender": "ai",
        "message": "您好，张伟！我是贵公司的AI招聘助手。我们看到您投递了高级前端工程师的职位，您的简历非常出色！能否简单介绍一下您在字节跳动的工作经历？",
        "timestamp": "2025-01-13T08:30:00Z"
      },
      {
        "id": "46000000-0000-0000-0000-000000000002",
        "sender": "candidate",
        "message": "您好！我在字节跳动主要负责抖音创作者平台的前端开发，从0到1搭建了整个平台，目前支持百万级创作者使用。主要技术栈是React、TypeScript和Next.js。",
        "timestamp": "2025-01-13T08:32:15Z"
      }
    ],

    "createdAt": "2025-01-27T10:30:00Z",
    "updatedAt": "2025-01-27T10:30:00Z"
  }
}
```

### 📊 更新简历状态

**PATCH** `/resumes/{resume_id}/status`

更新简历处理状态

**请求体**:
```json
{
  "status": "pending|reviewing|interview|offered|rejected"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "状态更新成功",
  "data": {
    "id": "40000000-0000-0000-0000-000000000001",
    "status": "reviewing",
    "updatedAt": "2025-01-27T11:00:00Z"
  }
}
```

### 🤖 AI简历匹配

**POST** `/resumes/{resume_id}/ai-match`

对简历进行AI智能匹配分析

**请求体**:
```json
{
  "jobId": "30000000-0000-0000-0000-000000000001"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "AI匹配完成",
  "data": {
    "isMatch": true,
    "score": 92,
    "reason": "候选人具备丰富的前端开发经验，技术栈完全匹配，有大厂背景，项目经验丰富。",
    "strengths": ["技术栈匹配", "大厂背景", "项目经验丰富"],
    "weaknesses": ["薪资期望略高"],
    "recommendation": "强烈推荐安排技术面试"
  }
}
```

### 📧 发送邮件

**POST** `/resumes/{resume_id}/send-email`

向候选人发送邮件

**请求体**:
```json
{
  "subject": "面试邀请",
  "content": "您好！我们邀请您来参加技术面试，时间安排在..."
}
```

---

## 渠道管理

### 📢 获取渠道列表

**GET** `/channels`

获取招聘渠道列表，管理员可查看所有渠道，HR只能查看自己创建的渠道

**查询参数**:
- `page` (int, optional): 页码，默认1
- `pageSize` (int, optional): 每页数量，默认10
- `search` (string, optional): 搜索关键词
- `status` (string, optional): 渠道状态筛选

**响应**:
```json
{
  "code": 200,
  "message": "获取渠道列表成功",
  "data": {
    "total": 20,
    "page": 1,
    "pageSize": 10,
    "items": [
      {
        "id": "50000000-0000-0000-0000-000000000001",
        "name": "智联招聘",
        "type": "job-board",
        "status": "active",
        "applicantsCount": 150,
        "annualCost": 50000.00,
        "costCurrency": "CNY",
        "contactPerson": "张经理",
        "contactEmail": "contact@zhaopin.com",
        "description": "综合性招聘网站，覆盖各行各业",
        "lastSyncAt": "2025-01-27T10:00:00Z",
        "createdAt": "2025-01-27T10:30:00Z",
        "updatedAt": "2025-01-27T10:30:00Z"
      }
    ]
  }
}
```

### ➕ 创建渠道

**POST** `/channels`

创建新的招聘渠道

**请求体**:
```json
{
  "name": "BOSS直聘",
  "type": "job-board",
  "status": "active",
  "annualCost": 80000.00,
  "costCurrency": "CNY",
  "contactPerson": "李经理",
  "contactEmail": "contact@bosszhipin.com",
  "description": "直聊模式招聘平台"
}
```

### ✏️ 更新渠道

**PUT** `/channels/{channel_id}`

更新渠道信息

### 🗑️ 删除渠道

**DELETE** `/channels/{channel_id}`

删除渠道

---

## 任务管理

### 📋 获取任务列表

**GET** `/tasks`

获取AI招聘任务列表，管理员可查看所有任务，HR只能查看自己的任务

**查询参数**:
- `page` (int, optional): 页码，默认1
- `pageSize` (int, optional): 每页数量，默认10
- `status` (string, optional): 任务状态筛选

**响应**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "total": 15,
    "page": 1,
    "pageSize": 10,
    "list": [
      {
        "id": "60000000-0000-0000-0000-000000000001",
        "jobId": "30000000-0000-0000-0000-000000000001",
        "jobTitle": "高级前端工程师",
        "status": "in-progress",
        "channelsPublished": 5,
        "totalChannels": 8,
        "resumesViewed": 120,
        "greetingsSent": 85,
        "conversationsActive": 12,
        "resumesRequested": 30,
        "resumesReceived": 18,
        "interviewsScheduled": 5,
        "completedAt": null,
        "createdAt": "2025-01-27T10:30:00Z",
        "updatedAt": "2025-01-27T10:30:00Z"
      }
    ]
  }
}
```

### ➕ 创建任务

**POST** `/tasks`

创建新的AI招聘任务

**请求体**:
```json
{
  "jobId": "30000000-0000-0000-0000-000000000001",
  "totalChannels": 10
}
```

---

## 错误处理

### 错误响应格式

所有错误都遵循统一的响应格式：

```json
{
  "code": 404,
  "message": "资源不存在",
  "data": null
}
```

### 常见错误代码

| 错误代码 | 说明 | 解决方案 |
|----------|------|----------|
| 400 | 请求参数错误 | 检查请求参数格式和必填字段 |
| 401 | 未授权访问 | 检查Token是否有效或是否已过期 |
| 403 | 权限不足 | 确认用户角色权限 |
| 404 | 资源不存在 | 检查资源ID是否正确 |
| 422 | 请求参数验证失败 | 检查参数类型和格式 |
| 500 | 服务器内部错误 | 联系技术支持 |

### 请求限制

- **认证接口**: 每分钟最多10次请求
- **查询接口**: 每分钟最多100次请求
- **创建/更新接口**: 每分钟最多50次请求
- **删除接口**: 每分钟最多20次请求

---

## 数据字典

### 状态值说明

**职位状态**:
- `open`: 开放招聘
- `closed`: 关闭招聘
- `draft`: 草稿

**简历状态**:
- `pending`: 待处理
- `reviewing`: 审核中
- `interview`: 面试中
- `offered`: 已发offer
- `rejected`: 已拒绝

**任务状态**:
- `not-started`: 未开始
- `in-progress`: 进行中
- `paused`: 已暂停
- `completed`: 已完成

**渠道状态**:
- `active`: 激活
- `inactive`: 停用

**渠道类型**:
- `job-board`: 招聘网站
- `social-media`: 社交媒体
- `referral`: 内推
- `agency`: 猎头
- `website`: 官网

**职位类型**:
- `full-time`: 全职
- `part-time`: 兼职
- `contract`: 合同
- `intern`: 实习

**性别**:
- `male`: 男
- `female`: 女
- `unlimited`: 不限

---

## 测试账号

### 管理员账号
- **邮箱**: `li@demo.com`
- **密码**: `123456`
- **权限**: 可查看所有租户数据

### HR账号
- **邮箱**: `wang@demo.com`
- **密码**: `123456`
- **权限**: 只能查看自己负责的数据

---

*文档最后更新时间: 2025-01-27*
*API版本: v1*