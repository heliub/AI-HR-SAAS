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
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "10000000-0000-0000-0000-000000000004",
      "name": "李技术总监",
      "email": "li@demo.com",
      "role": "admin",
      "avatar": null
    }
  }
}
```

#### 用户登出
**POST** `/auth/logout`

**请求体**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应**:
```json
{
  "code": 200,
  "message": "登出成功",
  "data": null
}
```

#### 获取当前用户信息
**GET** `/auth/me`

**请求头**:
```http
Authorization: Bearer YOUR_TOKEN
```

**响应**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "id": "10000000-0000-0000-0000-000000000004",
    "name": "李技术总监",
    "email": "li@demo.com",
    "role": "admin",
    "avatar": null
  }
}
```

---

## 用户管理

### 👤 获取当前用户信息

**GET** `/auth/me`

获取当前登录用户的详细信息

**响应**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "id": "10000000-0000-0000-0000-000000000004",
    "name": "李技术总监",
    "email": "li@demo.com",
    "role": "admin",
    "avatar": null
  }
}
```

### ✏️ 更新个人信息

**PUT** `/account/profile`

更新当前用户信息

**请求体**:
```json
{
  "name": "新用户名",
  "avatar": "https://example.com/new-avatar.jpg"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "个人信息更新成功",
  "data": null
}
```

### 🔒 更新密码

**PUT** `/account/password`

更新用户密码

**请求体**:
```json
{
  "currentPassword": "old-password123",
  "newPassword": "new-password456"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "密码更新成功",
  "data": null
}
```

### 📷 上传头像

**POST** `/account/avatar`

上传用户头像

**请求体**: `multipart/form-data`
- `file`: 图片文件

**响应**:
```json
{
  "code": 200,
  "message": "头像上传成功",
  "data": {
    "avatarUrl": "https://example.com/avatars/user1.jpg"
  }
}
```

### 🔔 更新通知设置

**POST** `/account/notifications`

更新通知偏好设置

**请求体**:
```json
{
  "emailNotifications": true,
  "taskReminders": true
}
```

**响应**:
```json
{
  "code": 200,
  "message": "通知设置更新成功",
  "data": null
}
```

---

## 职位管理

### 📋 获取职位列表

**GET** `/jobs`

获取职位列表 - 优化版本，使用JOIN查询解决N+1性能问题
- **管理员 (`admin`角色)**: 可查看租户内所有职位
- **普通HR (`hr`角色)**: 只能查看自己创建的职位
- **性能优化**: 通过LEFT JOIN查询一次性获取职位和关联渠道信息，避免N+1查询问题

**查询参数**:
- `page` (int, optional): 页码，默认1，最小值1
- `pageSize` (int, optional): 每页数量，默认10，范围1-100
- `search` (string, optional): 搜索关键词（标题、公司、描述）
- `status` (string, optional): 职位状态筛选
- `company` (string, optional): 公司名称筛选
- `category` (string, optional): 职位类别筛选 (如: Software Development, Design, Sales)
- `workplaceType` (string, optional): 工作场所类型筛选 (On-site/Hybrid/Remote)

**请求示例**:
```http
GET /api/v1/jobs?page=1&pageSize=10&search=前端&status=open&company=字节跳动&workplaceType=Hybrid
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
        "company": "字节跳动",
        "location": "北京",
        "type": "full-time",
        "workplaceType": "Hybrid",
        "status": "open",
        "minSalary": 2500000,
        "maxSalary": 4500000,
        "payType": "Monthly",
        "payCurrency": "CNY",
        "payShownOnAd": true,
        "salary": "25K-45K",
        "description": "负责公司核心产品的前端开发工作...",
        "requirements": "React,TypeScript,5年以上经验",
        "category": "Software Development",
        "recruitmentInvitation": "我们正在寻找优秀的前端工程师加入团队...",
        "education": "本科及以上",
        "preferredSchools": "清华大学,北京大学",
        "applicantsCount": 15,
        "channels": [
          "50000000-0000-0000-0000-000000000001",
          "50000000-0000-0000-0000-000000000002"
        ],
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
    "company": "字节跳动",
    "location": "北京",
    "type": "full-time",
    "workplaceType": "Hybrid",
    "status": "open",
    "minSalary": 2500000,
    "maxSalary": 4500000,
    "payType": "Monthly",
    "payCurrency": "CNY",
    "payShownOnAd": true,
    "salary": "25K-45K",
    "description": "负责公司核心产品的前端开发工作，参与产品需求分析和技术方案设计...",
    "requirements": "React,TypeScript,5年以上经验,大厂背景优先",
    "category": "Software Development",
    "recruitmentInvitation": "我们正在寻找优秀的前端工程师加入我们的技术团队！你将有机会参与创新项目...",
    "education": "本科及以上",
    "preferredSchools": "清华大学,北京大学",
    "applicantsCount": 15,
    "channels": [
      "50000000-0000-0000-0000-000000000001",
      "50000000-0000-0000-0000-000000000002"
    ],
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

创建新职位
- 自动设置当前用户为创建者(`created_by`、`user_id`)
- 自动设置租户ID(`tenant_id`)
- 默认状态为`draft`（草稿）

**请求体**:
```json
{
  "title": "高级后端工程师",
  "company": "字节跳动",
  "location": "北京",
  "type": "full-time",
  "workplaceType": "Hybrid",
  "status": "draft",
  "minSalary": 3000000,
  "maxSalary": 5000000,
  "payType": "Monthly",
  "payCurrency": "CNY",
  "payShownOnAd": true,
  "description": "负责后端服务开发和架构设计，参与系统架构优化...",
  "requirements": "Java,Spring Boot,微服务；3年以上相关开发经验；熟悉分布式系统设计",
  "category": "Software Development",
  "recruitmentInvitation": "寻找优秀的后端工程师加入我们的技术团队...",
  "education": "本科及以上",
  "preferredSchools": "清华大学,北京大学,浙江大学",
  "applicantsCount": 0,
  "channels": [
    "50000000-0000-0000-0000-000000000001",
    "50000000-0000-0000-0000-000000000002"
  ]
}
```

**字段说明**:
- `title` (string, required): 职位标题，1-200字符
- `company` (string, optional): 公司名称，最大200字符
- `location` (string, required): 工作地点，1-100字符
- `type` (string, required): 职位类型 (full-time/part-time/contract/intern)
- `workplaceType` (string, optional): 工作场所类型 (On-site/Hybrid/Remote)
- `status` (string, optional): 职位状态，默认为"draft" (open/closed/draft)
- `minSalary` (integer, optional): 最低薪资（分为单位，不能为负数）
- `maxSalary` (integer, optional): 最高薪资（分为单位，不能低于最低薪资）
- `payType` (string, optional): 薪资类型 (Hourly/Monthly/Annual/Annual plus commission)
- `payCurrency` (string, optional): 薪资货币，默认CNY
- `payShownOnAd` (boolean, optional): 是否在招聘广告中显示薪资
- `description` (string, optional): 职位详细描述
- `requirements` (string, optional): 职位要求，多个要求用分号(;)分隔
- `category` (string, optional): 职位类别，最大100字符
- `recruitmentInvitation` (string, optional): 招聘邀请语
- `education` (string, optional): 学历要求
- `preferredSchools` (string, optional): 偏好学校，多个学校用逗号(,)分隔
- `applicantsCount` (integer, optional): 申请人数，默认为0，不能为负数
- `channels` (array, optional): 关联的渠道ID列表，支持UUID数组格式，用于建立职位与招聘渠道的多对多关联

**响应**:
```json
{
  "code": 200,
  "message": "职位创建成功",
  "data": {
    "id": "30000000-0000-0000-0000-000000000002",
    "title": "高级后端工程师",
    "company": "字节跳动",
    "status": "draft",
    "channels": [
      "50000000-0000-0000-0000-000000000001",
      "50000000-0000-0000-0000-000000000002"
    ],
    "createdAt": "2025-01-27T11:00:00Z",
    "userId": "10000000-0000-0000-0000-000000000004",
    "createdBy": "10000000-0000-0000-0000-000000000004"
  }
}
```

### ✏️ 更新职位

**PUT** `/jobs/{job_id}`

更新指定职位信息
- **管理员 (`admin`角色)**: 可以更新任何职位
- **普通HR (`hr`角色)**: 只能更新自己创建的职位
- 系统自动处理时间戳更新（`updatedAt`字段）

**请求体**:
```json
{
  "title": "更新的职位名称",
  "company": "更新的公司名称",
  "location": "更新的工作地点",
  "type": "full-time",
  "workplaceType": "Hybrid",
  "minSalary": 2800000,
  "maxSalary": 4800000,
  "payType": "Monthly",
  "payCurrency": "CNY",
  "payShownOnAd": true,
  "description": "更新的职位描述，包含详细的职责和要求...",
  "requirements": "React,TypeScript；5年以上前端开发经验；有大型项目经验",
  "category": "Software Development",
  "recruitmentInvitation": "寻找优秀的前端工程师加入团队...",
  "education": "本科及以上",
  "preferredSchools": "清华大学,北京大学",
  "applicantsCount": 15,
  "channels": [
    "50000000-0000-0000-0000-000000000003",
    "50000000-0000-0000-0000-000000000004"
  ]
}
```

**字段说明**:
- 只能更新指定的字段，状态(`status`)和时间戳等字段由系统自动处理
- 更新时间(`updatedAt`)会自动设置为当前时间
- 薪资验证：最低薪资不能为负数，最高薪资不能低于最低薪资
- 申请人数验证：不能为负数
- 渠道关联：提供`channels`字段时会完全替换现有关联，空数组表示取消所有关联

### 🗑️ 删除职位

**DELETE** `/jobs/{job_id}`

删除指定职位
- **管理员 (`admin`角色)**: 可以删除任何职位
- **普通HR (`hr`角色)**: 只能删除自己创建的职位
- 删除操作不可逆，请谨慎操作

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

AI智能生成职位描述和要求，根据多个参数智能生成完整的职位信息

**请求体**:
```json
{
  "title": "高级前端工程师",
  "type": "full-time",
  "workplaceType": "Hybrid",
  "payCurrency": "CNY",
  "location": "北京"
}
```

**字段说明**:
- `title` (string, required): 职位标题，用于智能生成相关内容
- `type` (string, required): 职位类型 (full-time/part-time/contract/intern)
- `workplaceType` (string, optional): 工作场所类型 (On-site/Hybrid/Remote)
- `payCurrency` (string, optional): 薪资货币，默认CNY
- `location` (string, optional): 工作地点，如未提供则根据职位类型智能推荐

**响应**:
```json
{
  "code": 200,
  "message": "生成成功",
  "data": {
    "company": null,
    "location": "北京",
    "workplaceType": "Hybrid",
    "minSalary": 2000000,
    "maxSalary": 4500000,
    "payType": "Monthly",
    "payCurrency": "CNY",
    "payShownOnAd": true,
    "description": "职位描述：\n1. 负责公司高级前端工程师相关的开发工作，参与产品需求分析和技术方案设计\n2. 编写高质量、可维护的代码，完成核心功能模块开发\n3. 参与代码审查，确保代码质量和团队技术水平提升\n4. 解决开发过程中的技术难题，优化系统性能\n5. 与产品、设计、测试团队密切配合，确保项目按时高质量交付\n\n任职要求：\n• 3年以上相关开发经验，有大型项目经验者优先\n• 熟练掌握相关技术栈和开发工具\n• 具备良好的编程习惯和代码规范意识\n• 有较强的学习能力和技术热情",
    "requirements": "3年以上相关开发经验，有大型项目经验者优先；熟练掌握相关技术栈和开发工具；具备良好的编程习惯和代码规范意识；有较强的学习能力和技术热情",
    "category": "Software Development",
    "recruitmentInvitation": "我们正在寻找优秀的高级前端工程师加入我们的技术团队！你将有机会参与创新项目，与技术大牛一起成长，享受有竞争力的薪酬福利和良好的职业发展空间。",
    "education": "本科及以上"
  }
}
```

**智能生成特性**:
- ✅ 根据职位标题智能识别职位类别（技术/产品/HR/通用）
- ✅ 根据输入参数定制生成内容（地点、工作场所、货币）
- ✅ 智能匹配薪资范围和职位要求
- ✅ 生成完整的职位描述、要求和招聘邀请语

**不同职位类型的生成示例**:
```json
// 技术类职位 - 高薪资范围
{
  "title": "高级前端工程师",
  "type": "full-time",
  "workplaceType": "Hybrid",
  "payCurrency": "USD",
  "location": "硅谷"
}

// 产品类职位 - 中等薪资范围
{
  "title": "产品经理",
  "type": "full-time",
  "workplaceType": "Remote",
  "payCurrency": "CNY",
  "location": "上海"
}

// HR类职位 - 偏向现场办公
{
  "title": "招聘专员",
  "type": "full-time",
  "workplaceType": "On-site",
  "payCurrency": "CNY",
  "location": "北京"
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
        "skills": "React,TypeScript,Node.js,Next.js",
        "submittedAt": "2025-01-13T10:30:00Z",
        "conversationSummary": "候选人张伟在字节跳动有丰富的前端开发经验...",
        "isMatch": true,
        "matchConclusion": "候选人具备丰富的前端开发经验，技术栈完全匹配，有大厂背景，项目经验丰富。强烈推荐安排技术面试。",
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
    "skills": "React,TypeScript,Node.js,Next.js",
    "submittedAt": "2025-01-13T10:30:00Z",
    "conversationSummary": "候选人张伟在字节跳动有丰富的前端开发经验，主导开发了抖音创作者平台...",
    "isMatch": true,
    "matchConclusion": "候选人具备丰富的前端开发经验，技术栈完全匹配，有大厂背景，项目经验丰富。强烈推荐安排技术面试。",
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
        "technologies": "React,TypeScript,Next.js,Node.js,GraphQL"
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
      "preferredLocations": "北京,上海",
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
        "strengths": "技术栈匹配,大厂背景,项目经验丰富,性能优化经验",
        "weaknesses": "薪资期望略高于预算",
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
    "strengths": "技术栈匹配,大厂背景,项目经验丰富",
    "weaknesses": "薪资期望略高",
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
- 默认过滤掉已删除的渠道
- 管理员 (`admin`角色): 可查看租户内所有渠道
- 普通HR (`hr`角色): 只能查看自己创建的渠道

**查询参数**:
- `page` (int, optional): 页码，默认1
- `pageSize` (int, optional): 每页数量，默认10
- `search` (string, optional): 搜索关键词
- `status` (string, optional): 渠道状态筛选 (active, inactive, deleted)

**响应**:
```json
{
  "code": 200,
  "message": "获取渠道列表成功",
  "data": {
    "total": 20,
    "page": 1,
    "pageSize": 10,
    "list": [
      {
        "id": "50000000-0000-0000-0000-000000001",
        "name": "智联招聘",
        "type": "job-board",
        "status": "active",
        "cost": "50000.00",
        "costCurrency": "CNY",
        "contactPerson": "张经理",
        "contactEmail": "contact@zhaopin.com",
        "description": "综合性招聘网站，覆盖各行各业",
        "applicantsCount": 150,
        "lastSync": "2025-01-27T10:00:00Z",
        "userId": "10000000-0000-0000-0000-000000004",
        "createdAt": "2025-01-27T10:30:00Z",
        "updatedAt": "2025-01-27T10:30:00Z"
      }
    ]
  }
}
```

### 🔍 获取渠道详情

**GET** `/channels/{channel_id}`

获取指定渠道的详细信息
- 已删除的渠道无法访问

**路径参数**:
- `channel_id` (UUID): 渠道ID

**响应**:
```json
{
  "code": 200,
  "message": "获取渠道详情成功",
  "data": {
    "id": "50000000-0000-0000-0000-000000001",
    "name": "智联招聘",
    "status": "active",
    "cost": "50000.00",
    "costCurrency": "CNY",
    "contactPerson": "张经理",
    "contactEmail": "contact@zhaopin.com",
    "description": "综合性招聘网站，覆盖各行各业",
    "applicantsCount": 150,
    "lastSync": "2025-01-27T10:00:00Z",
    "userId": "10000000-0000-0000-0000-000000004",
    "createdAt": "2025-01-27T10:30:00Z",
    "updatedAt": "2025-01-27T10:30:00Z"
  }
}
```

### ➕ 创建渠道

**POST** `/channels/create`

创建新的招聘渠道
- 自动设置当前用户为创建者
- 自动设置租户ID

**请求体**:
```json
{
  "name": "BOSS直聘",
  "status": "active",
  "cost": "80000.00",
  "apiKey":"222xx",
  "costCurrency": "CNY",
  "contactPerson": "李经理",
  "contactEmail": "contact@bosszhipin.com",
  "description": "直聊模式招聘平台"
}
```

**字段说明**:
- `name` (string, required): 渠道名称，1-100字符
- `status` (string, optional): 渠道状态，默认为"active" (active/inactive)
- `cost` (string, optional): 年度成本，字符串格式以避免精度问题
- `costCurrency` (string, optional): 成本货币，默认为"CNY"
- `apiKey` (string, optional): API密钥，仅用于创建和更新，不在响应中返回
- `contactPerson` (string, optional): 联系人姓名
- `contactEmail` (string, optional): 联系邮箱，可为空字符串
- `description` (string, optional): 渠道描述

**响应**:
```json
{
  "code": 200,
  "message": "渠道创建成功",
  "data": {
    "id": "50000000-0000-0000-0000-000000002",
    "name": "BOSS直聘",
    "status": "active",
    "cost": "80000.00",
    "costCurrency": "CNY",
    "contactPerson": "李经理",
    "contactEmail": "contact@bosszhipin.com",
    "description": "直聊模式招聘平台",
    "applicantsCount": 0,
    "userId": "10000000-0000-0000-0000-000000004",
    "createdAt": "2025-01-27T11:00:00Z",
    "updatedAt": "2025-01-27T11:00:00Z"
  }
}
```

### ✏️ 更新渠道

**PUT** `/channels/{channel_id}`

更新指定渠道信息
- 管理员 (`admin`角色): 可以更新任何渠道
- 普通HR (`hr`角色): 只能更新自己创建的渠道
- 已删除的渠道无法更新

**请求体**:
```json
{
  "name": "更新的渠道名称",
  "status": "inactive",
  "cost": "90000.00",
  "costCurrency": "USD",
  "apiKey": "22xxx",
  "contactPerson": "王经理",
  "contactEmail": "new-contact@example.com",
  "description": "更新的渠道描述"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "渠道更新成功",
  "data": {
    "id": "50000000-0000-0000-0000-000000001",
    "name": "更新的渠道名称",
    "status": "inactive",
    "cost": "90000.00",
    "costCurrency": "USD",
    "contactPerson": "王经理",
    "contactEmail": "new-contact@example.com",
    "description": "更新的渠道描述",
    "applicantsCount": 150,
    "lastSync": "2025-01-27T10:00:00Z",
    "userId": "10000000-0000-0000-0000-000000004",
    "createdAt": "2025-01-27T10:30:00Z",
    "updatedAt": "2025-01-27T11:30:00Z"
  }
}
```

### 🗑️ 删除渠道

**DELETE** `/channels/{channel_id}`

逻辑删除指定渠道（将状态设置为deleted）
- 管理员 (`admin`角色): 可以删除任何渠道
- 普通HR (`hr`角色): 只能删除自己创建的渠道
- 删除操作为逻辑删除，数据仍保留在数据库中

**响应**:
```json
{
  "code": 200,
  "message": "渠道删除成功"
}
```

### 🔄 更新渠道状态

**PATCH** `/channels/{channel_id}/status`

更新渠道状态
- 管理员 (`admin`角色): 可以更新任何渠道状态
- 普通HR (`hr`角色): 只能更新自己创建的渠道状态
- 已删除的渠道无法更新状态

**请求体**:
```json
{
  "status": "active"
}
```

**字段说明**:
- `status` (string, required): 渠道状态 (active, inactive, deleted)

**响应**:
```json
{
  "code": 200,
  "message": "渠道状态更新成功",
  "data": {
    "id": "50000000-0000-0000-0000-000000001",
    "name": "智联招聘",
    "type": "job-board",
    "status": "active",
    "cost": "50000.00",
    "costCurrency": "CNY",
    "contactPerson": "张经理",
    "contactEmail": "contact@zhaopin.com",
    "description": "综合性招聘网站，覆盖各行各业",
    "applicantsCount": 150,
    "lastSync": "2025-01-27T10:00:00Z",
    "userId": "10000000-0000-0000-0000-000000004",
    "createdAt": "2025-01-27T10:30:00Z",
    "updatedAt": "2025-01-27T11:30:00Z"
  }
}
```

### 🔄 同步渠道数据

**POST** `/channels/{channel_id}/sync`

同步渠道数据
- 已删除的渠道无法同步

**响应**:
```json
{
  "code": 200,
  "message": "同步成功",
  "data": {
    "newResumes": 5,
    "syncedAt": "2025-01-27T12:00:00Z"
  }
}
```

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

## AI聊天管理

### 💬 获取聊天会话列表

**GET** `/chat/sessions`

获取用户的聊天会话列表

**查询参数**:
- `page` (int, optional): 页码，默认1，最小值1
- `pageSize` (int, optional): 每页数量，默认10，范围1-100

**响应**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "total": 5,
    "page": 1,
    "pageSize": 10,
    "list": [
      {
        "id": "70000000-0000-0000-0000-000000000001",
        "title": "招聘咨询 - 前端工程师",
        "userId": "10000000-0000-0000-0000-000000000004",
        "createdAt": "2025-01-27T10:30:00Z",
        "updatedAt": "2025-01-27T15:30:00Z"
      }
    ]
  }
}
```

### ➕ 创建新会话

**POST** `/chat/sessions`

创建新的聊天会话

**请求体**:
```json
{
  "title": "新对话"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "会话创建成功",
  "data": {
    "id": "70000000-0000-0000-0000-000000000002",
    "title": "新对话",
    "userId": "10000000-0000-0000-0000-000000000004",
    "createdAt": "2025-01-27T16:00:00Z",
    "updatedAt": "2025-01-27T16:00:00Z"
  }
}
```

### 📨 获取聊天历史

**GET** `/chat/sessions/{session_id}/messages`

获取指定会话的聊天历史记录

**路径参数**:
- `session_id` (UUID): 会话ID

**响应**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "messages": [
      {
        "id": "71000000-0000-0000-0000-000000000001",
        "role": "assistant",
        "content": "你好！我是AI招聘助手，有什么可以帮助你的吗？",
        "timestamp": "2025-01-27T10:30:00Z"
      },
      {
        "id": "71000000-0000-0000-0000-000000000002",
        "role": "user",
        "content": "帮我筛选一下前端工程师的简历",
        "timestamp": "2025-01-27T10:31:00Z"
      }
    ]
  }
}
```

### 📤 发送消息

**POST** `/chat/sessions/{session_id}/messages`

向指定会话发送消息

**路径参数**:
- `session_id` (UUID): 会话ID

**请求体**:
```json
{
  "content": "帮我筛选一下前端工程师的简历"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "id": "71000000-0000-0000-0000-000000000003",
    "role": "assistant",
    "content": "我已收到您的简历筛选请求。正在为您分析数据库中的简历匹配情况，请稍等...",
    "timestamp": "2025-01-27T10:31:30Z"
  }
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
| 403 | 权限不足 | 确认用户角色权限，管理员才能操作他人的职位 |
| 404 | 资源不存在 | 检查资源ID是否正确 |
| 422 | 请求参数验证失败 | 检查参数类型和格式（如薪资不能为负数） |
| 500 | 服务器内部错误 | 联系技术支持 |

### 请求限制

- **认证接口**: 每分钟最多10次请求
- **查询接口**: 每分钟最多100次请求
- **创建/更新接口**: 每分钟最多50次请求
- **删除接口**: 每分钟最多20次请求

---

## 字段格式说明

### 字符串数组字段

以下字段现在使用逗号分隔的字符串格式存储多个值：

**技术类字段**:
- `requirements`: 职位要求，多个要求用分号(;)分隔
- `skills`: 技能列表，多个技能用逗号(,)分隔
- `technologies`: 技术栈，多个技术用逗号(,)分隔

**偏好类字段**:
- `preferredSchools`: 偏好学校，多个学校用逗号(,)分隔
- `preferredLocations`: 期望工作地点，多个地点用逗号(,)分隔

**AI分析字段**:
- `strengths`: 优势列表，多个优势用逗号(,)分隔
- `weaknesses`: 劣势列表，多个劣势用逗号(,)分隔

**渠道关联字段**:
- `channels`: 关联的招聘渠道ID列表，支持UUID数组格式，通过job_channels中间表建立多对多关联

**AI匹配字段**:
- `isMatch`: 布尔值，表示简历是否匹配职位要求（基于AI分析结果）
- `matchConclusion`: 文本，存储AI分析的匹配结论和建议

**示例**:
```json
{
  "requirements": "3年以上相关开发经验；熟练掌握相关技术栈；具备良好的编程习惯",
  "skills": "React,TypeScript,Node.js,Next.js",
  "preferredSchools": "清华大学,北京大学,浙江大学",
  "strengths": "技术栈匹配,大厂背景,项目经验丰富",
  "isMatch": true,
  "matchConclusion": "候选人具备丰富的前端开发经验，技术栈完全匹配，有大厂背景，项目经验丰富。强烈推荐安排技术面试。",
  "channels": [
    "50000000-0000-0000-0000-000000000001",
    "50000000-0000-0000-0000-000000000002"
  ]
}
```

**数据类型说明**:
- **字符串数组字段**: 使用逗号/分号分隔的单个字符串字段存储（如requirements, skills, preferredSchools等）
- **UUID数组字段**: 使用真正的JSON数组格式存储（如channels字段），通过数据库中间表实现关联
- **布尔字段**: 使用布尔值存储（如isMatch字段）
- **文本字段**: 使用文本类型存储（如matchConclusion字段）

---

## 性能优化说明

### 🚀 N+1查询优化

**问题描述**:
职位列表查询原本存在N+1查询性能问题：
- 1次查询获取N个职位
- N次查询获取每个职位的渠道信息
- 总计：1+N次数据库查询

**优化方案**:
使用SQLAlchemy LEFT JOIN查询一次性获取职位和关联渠道信息：

```python
# 优化查询示例
query = (
    select(Job, JobChannel.channel_id)
    .select_from(Job)
    .outerjoin(JobChannel, and_(
        Job.id == JobChannel.job_id,
        JobChannel.tenant_id == tenant_id
    ))
    .where(and_(*conditions))
    .order_by(Job.created_at.desc())
)
```

**性能提升效果**:
| 职位数量 | 优化前查询次数 | 优化后查询次数 | 性能提升 |
|---------|---------------|---------------|----------|
| 10个职位 | 11次 | 1次 | 91% |
| 50个职位 | 51次 | 1次 | 98% |
| 100个职位 | 101次 | 1次 | 99% |

**优势**:
- ✅ 显著减少数据库查询次数
- ✅ 提升API响应速度
- ✅ 保持多租户数据隔离安全
- ✅ 不影响现有API响应格式

---

## 渠道关联使用说明

### 渠道关联机制

职位与招聘渠道通过`job_channels`中间表建立多对多关联关系：

**创建职位时关联渠道**:
```json
{
  "title": "高级前端工程师",
  "company": "字节跳动",
  "channels": [
    "50000000-0000-0000-0000-000000000001",  // 智联招聘
    "50000000-0000-0000-0000-000000000002"   // BOSS直聘
  ]
}
```

**更新职位渠道关联**:
```json
{
  "channels": [
    "50000000-0000-0000-0000-000000000003",  // 猎聘网站
    "50000000-0000-0000-0000-000000000004"   // 内推渠道
  ]
}
```

**渠道关联说明**:
- ✅ 支持关联多个招聘渠道
- ✅ 创建职位时可关联多个渠道
- ✅ 更新时完全替换现有关联（先删除再创建）
- ✅ 空数组`[]`表示取消所有渠道关联
- ✅ 不提供`channels`字段时保持现有关联不变
- ✅ 返回数据中包含完整的渠道ID列表

**渠道类型**:
- `job-board`: 招聘网站（如智联招聘、前程无忧）
- `social-media`: 社交媒体（如LinkedIn）
- `referral`: 内推渠道
- `agency`: 猎头服务
- `website`: 官网招聘

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
- `deleted`: 已删除（逻辑删除）

**职位类型**:
- `full-time`: 全职
- `part-time`: 兼职
- `contract`: 合同
- `intern`: 实习

**工作场所类型**:
- `On-site`: 现场办公
- `Hybrid`: 混合办公
- `Remote`: 远程办公

**薪资类型**:
- `Hourly rate`: 小时费率
- `Monthly salary`: 月薪
- `Annual salary`: 年薪
- `Annual plus commission`: 年薪+提成

**薪资货币**:
- `AUD`: 澳元
- `HKD`: 港币
- `IDR`: 印尼盾
- `MYR`: 马来西亚林吉特
- `NZD`: 新西兰元
- `PHP`: 菲律宾比索
- `SGD`: 新加坡元
- `THB`: 泰铢
- `USD`: 美元
- `CNY`: 人民币

**职位类别**:
- `Software Development`: 软件开发
- `Engineering`: 工程技术
- `Product Management`: 产品管理
- `Design`: 设计
- `Sales`: 销售
- `Marketing`: 市场营销
- `Human Resources`: 人力资源
- `General Business`: 综合商业

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

*文档最后更新时间: 2025-01-28*
*API版本: v1*