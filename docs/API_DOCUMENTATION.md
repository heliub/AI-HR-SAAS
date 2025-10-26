# AI HR SaaS 接口文档

## 目录
- [1. 认证模块](#1-认证模块)
- [2. 职位管理模块](#2-职位管理模块)
- [3. 简历管理模块](#3-简历管理模块)
- [4. 招聘渠道管理模块](#4-招聘渠道管理模块)
- [5. AI招聘任务模块](#5-ai招聘任务模块)
- [6. 面试管理模块](#6-面试管理模块)
- [7. AI聊天模块](#7-ai聊天模块)
- [8. 账户设置模块](#8-账户设置模块)
- [9. 统计数据模块](#9-统计数据模块)

---

## 1. 认证模块

### 1.1 用户登录
**接口地址**: `POST /api/auth/login`

**入参**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**出参**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "1",
      "name": "张三",
      "email": "user@example.com",
      "role": "hr",
      "avatar": "https://example.com/avatar.jpg"
    }
  }
}
```

### 1.2 用户登出
**接口地址**: `POST /api/auth/logout`

**入参**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**出参**:
```json
{
  "code": 200,
  "message": "登出成功"
}
```

### 1.3 获取当前用户信息
**接口地址**: `GET /api/auth/me`

**请求头**:
```
Authorization: Bearer {token}
```

**出参**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "id": "1",
    "name": "张三",
    "email": "user@example.com",
    "role": "hr",
    "avatar": "https://example.com/avatar.jpg"
  }
}
```

---

## 2. 职位管理模块

### 2.1 获取职位列表
**接口地址**: `GET /api/jobs`

**查询参数**:
- `page`: 页码 (默认: 1)
- `pageSize`: 每页数量 (默认: 10)
- `search`: 搜索关键词
- `status`: 职位状态 (open/closed/draft)
- `department`: 部门筛选

**出参**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "list": [
      {
        "id": "1",
        "title": "高级前端工程师",
        "department": "技术部",
        "location": "北京",
        "type": "full-time",
        "status": "open",
        "salary": "25K-40K",
        "description": "负责公司核心产品的前端开发工作",
        "requirements": ["5年以上前端开发经验", "精通React/Vue"],
        "createdAt": "2025-01-05T08:00:00Z",
        "applicants": 23,
        "ageRange": "25-35岁",
        "gender": "unlimited",
        "education": "本科及以上",
        "preferredSchools": ["清华大学", "北京大学"],
        "jobLevel": "P6-P7",
        "recruitmentInvitation": "我们正在寻找有激情的前端工程师...",
        "publishedChannels": ["1", "3"]
      }
    ],
    "total": 100,
    "page": 1,
    "pageSize": 10
  }
}
```

### 2.2 获取职位详情
**接口地址**: `GET /api/jobs/:id`

**出参**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "id": "1",
    "title": "高级前端工程师",
    "department": "技术部",
    "location": "北京",
    "type": "full-time",
    "status": "open",
    "salary": "25K-40K",
    "description": "负责公司核心产品的前端开发工作",
    "requirements": ["5年以上前端开发经验", "精通React/Vue"],
    "createdAt": "2025-01-05T08:00:00Z",
    "applicants": 23,
    "ageRange": "25-35岁",
    "gender": "unlimited",
    "education": "本科及以上",
    "preferredSchools": ["清华大学", "北京大学"],
    "jobLevel": "P6-P7",
    "recruitmentInvitation": "我们正在寻找有激情的前端工程师...",
    "publishedChannels": ["1", "3"]
  }
}
```

### 2.3 创建职位
**接口地址**: `POST /api/jobs`

**入参**:
```json
{
  "title": "高级前端工程师",
  "department": "技术部",
  "location": "北京",
  "type": "full-time",
  "status": "draft",
  "salary": "25K-40K",
  "description": "负责公司核心产品的前端开发工作",
  "requirements": ["5年以上前端开发经验", "精通React/Vue"],
  "ageRange": "25-35岁",
  "gender": "unlimited",
  "education": "本科及以上",
  "preferredSchools": ["清华大学", "北京大学"],
  "jobLevel": "P6-P7",
  "recruitmentInvitation": "我们正在寻找有激情的前端工程师...",
  "publishedChannels": ["1", "3"]
}
```

**出参**:
```json
{
  "code": 200,
  "message": "职位创建成功",
  "data": {
    "id": "1",
    "title": "高级前端工程师",
    "...": "..."
  }
}
```

### 2.4 更新职位
**接口地址**: `PUT /api/jobs/:id`

**入参**: 同创建职位

**出参**:
```json
{
  "code": 200,
  "message": "职位更新成功",
  "data": {
    "id": "1",
    "...": "..."
  }
}
```

### 2.5 删除职位
**接口地址**: `DELETE /api/jobs/:id`

**出参**:
```json
{
  "code": 200,
  "message": "职位删除成功"
}
```

### 2.6 更新职位状态
**接口地址**: `PATCH /api/jobs/:id/status`

**入参**:
```json
{
  "status": "open"
}
```

**出参**:
```json
{
  "code": 200,
  "message": "状态更新成功"
}
```

### 2.7 复制职位
**接口地址**: `POST /api/jobs/:id/duplicate`

**出参**:
```json
{
  "code": 200,
  "message": "职位复制成功",
  "data": {
    "id": "2",
    "title": "高级前端工程师 (副本)",
    "...": "..."
  }
}
```

### 2.8 AI生成职位描述
**接口地址**: `POST /api/jobs/ai-generate`

**入参**:
```json
{
  "title": "高级前端工程师",
  "jobLevel": "P6-P7"
}
```

**出参**:
```json
{
  "code": 200,
  "message": "生成成功",
  "data": {
    "department": "技术部",
    "location": "北京",
    "salary": "25K-40K",
    "description": "负责公司核心产品的前端开发工作...",
    "recruitmentInvitation": "我们正在寻找有激情的前端工程师...",
    "education": "本科及以上",
    "ageRange": "25-40岁"
  }
}
```

---

## 3. 简历管理模块

### 3.1 获取简历列表
**接口地址**: `GET /api/resumes`

**查询参数**:
- `page`: 页码 (默认: 1)
- `pageSize`: 每页数量 (默认: 10)
- `search`: 搜索关键词
- `status`: 简历状态 (pending/reviewing/interview/offered/rejected)
- `jobId`: 职位ID筛选

**出参**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "list": [
      {
        "id": "1",
        "candidateName": "张伟",
        "email": "zhangwei@example.com",
        "phone": "13800138000",
        "position": "高级前端工程师",
        "status": "pending",
        "source": "智联招聘",
        "submittedAt": "2025-01-13T10:30:00Z",
        "experience": "6年",
        "education": "本科",
        "skills": ["React", "TypeScript", "Node.js"],
        "age": 29,
        "gender": "male",
        "location": "北京",
        "school": "北京大学",
        "major": "计算机科学与技术",
        "aiMatch": {
          "isMatch": true,
          "score": 92,
          "reason": "候选人具备丰富的前端开发经验...",
          "strengths": ["6年前端开发经验", "熟练掌握React/TypeScript"],
          "weaknesses": ["缺少移动端开发经验"],
          "recommendation": "强烈推荐面试"
        }
      }
    ],
    "total": 50,
    "page": 1,
    "pageSize": 10
  }
}
```

### 3.2 获取简历详情
**接口地址**: `GET /api/resumes/:id`

**出参**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "id": "1",
    "candidateName": "张伟",
    "email": "zhangwei@example.com",
    "phone": "13800138000",
    "position": "高级前端工程师",
    "status": "pending",
    "source": "智联招聘",
    "submittedAt": "2025-01-13T10:30:00Z",
    "experience": "6年",
    "education": "本科",
    "skills": ["React", "TypeScript", "Node.js"],
    "age": 29,
    "gender": "male",
    "location": "北京",
    "school": "北京大学",
    "major": "计算机科学与技术",
    "resumeUrl": "https://example.com/resumes/1.pdf",
    "workHistory": [
      {
        "company": "字节跳动",
        "position": "高级前端工程师",
        "startDate": "2021-03",
        "endDate": "至今",
        "description": "负责抖音Web端核心功能开发"
      }
    ],
    "projectHistory": [
      {
        "name": "抖音创作者平台",
        "role": "前端负责人",
        "startDate": "2022-06",
        "endDate": "2024-12",
        "description": "从0到1搭建创作者平台",
        "technologies": ["React", "TypeScript", "Next.js"]
      }
    ],
    "educationHistory": [
      {
        "school": "北京大学",
        "degree": "本科",
        "major": "计算机科学与技术",
        "startDate": "2015-09",
        "endDate": "2019-06"
      }
    ],
    "jobPreferences": {
      "expectedSalary": "35K-45K",
      "preferredLocations": ["北京", "上海"],
      "jobType": "全职",
      "availableDate": "2025-02-01"
    },
    "aiMatch": {
      "isMatch": true,
      "score": 92,
      "reason": "候选人具备丰富的前端开发经验...",
      "strengths": ["6年前端开发经验", "熟练掌握React/TypeScript"],
      "weaknesses": ["缺少移动端开发经验"],
      "recommendation": "强烈推荐面试"
    },
    "aiChatHistory": [
      {
        "sender": "ai",
        "message": "您好，张伟！我是贵公司的AI招聘助手...",
        "timestamp": "2025-01-13T10:35:00Z"
      }
    ],
    "conversationSummary": "候选人张伟在字节跳动有丰富的前端开发经验..."
  }
}
```

### 3.3 更新简历状态
**接口地址**: `PATCH /api/resumes/:id/status`

**入参**:
```json
{
  "status": "reviewing"
}
```

**出参**:
```json
{
  "code": 200,
  "message": "状态更新成功"
}
```

### 3.4 AI匹配分析
**接口地址**: `POST /api/resumes/:id/ai-match`

**入参**:
```json
{
  "jobId": "1"
}
```

**出参**:
```json
{
  "code": 200,
  "message": "分析完成",
  "data": {
    "isMatch": true,
    "score": 92,
    "reason": "候选人具备丰富的前端开发经验...",
    "strengths": ["6年前端开发经验", "熟练掌握React/TypeScript"],
    "weaknesses": ["缺少移动端开发经验"],
    "recommendation": "强烈推荐面试"
  }
}
```

### 3.5 发送邮件
**接口地址**: `POST /api/resumes/:id/send-email`

**入参**:
```json
{
  "subject": "面试邀请",
  "content": "您好，我们想邀请您参加面试..."
}
```

**出参**:
```json
{
  "code": 200,
  "message": "邮件发送成功"
}
```

### 3.6 下载简历
**接口地址**: `GET /api/resumes/:id/download`

**出参**: PDF文件流

---

## 4. 招聘渠道管理模块

### 4.1 获取渠道列表
**接口地址**: `GET /api/channels`

**查询参数**:
- `page`: 页码
- `pageSize`: 每页数量
- `search`: 搜索关键词
- `status`: 渠道状态 (active/inactive)

**出参**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "list": [
      {
        "id": "1",
        "name": "智联招聘",
        "type": "job-board",
        "status": "active",
        "applicants": 156,
        "cost": "¥50,000/年",
        "lastSync": "2025-01-13T12:00:00Z",
        "apiKey": "xxx",
        "contactPerson": "张经理",
        "contactEmail": "zhang@zhaopin.com",
        "description": "国内领先的招聘平台"
      }
    ],
    "total": 5,
    "page": 1,
    "pageSize": 10
  }
}
```

### 4.2 创建渠道
**接口地址**: `POST /api/channels`

**入参**:
```json
{
  "name": "智联招聘",
  "type": "job-board",
  "status": "active",
  "cost": "¥50,000/年",
  "apiKey": "xxx",
  "contactPerson": "张经理",
  "contactEmail": "zhang@zhaopin.com",
  "description": "国内领先的招聘平台"
}
```

**出参**:
```json
{
  "code": 200,
  "message": "渠道创建成功",
  "data": {
    "id": "1",
    "...": "..."
  }
}
```

### 4.3 更新渠道
**接口地址**: `PUT /api/channels/:id`

**入参**: 同创建渠道

**出参**:
```json
{
  "code": 200,
  "message": "渠道更新成功"
}
```

### 4.4 删除渠道
**接口地址**: `DELETE /api/channels/:id`

**出参**:
```json
{
  "code": 200,
  "message": "渠道删除成功"
}
```

### 4.5 同步渠道数据
**接口地址**: `POST /api/channels/:id/sync`

**出参**:
```json
{
  "code": 200,
  "message": "同步成功",
  "data": {
    "newResumes": 5,
    "syncedAt": "2025-01-13T12:00:00Z"
  }
}
```

---

## 5. AI招聘任务模块

### 5.1 获取任务列表
**接口地址**: `GET /api/tasks`

**查询参数**:
- `page`: 页码
- `pageSize`: 每页数量
- `status`: 任务状态 (not-started/in-progress/paused/completed)

**出参**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "list": [
      {
        "id": "1",
        "jobId": "1",
        "jobTitle": "高级前端工程师",
        "status": "in-progress",
        "createdAt": "2025-01-10T09:00:00Z",
        "createdBy": "AI助手",
        "channelsPublished": 2,
        "totalChannels": 3,
        "resumesViewed": 45,
        "greetingsSent": 23,
        "conversationsActive": 12,
        "resumesRequested": 15,
        "resumesReceived": 8,
        "interviewsScheduled": 3
      }
    ],
    "total": 3,
    "page": 1,
    "pageSize": 10
  }
}
```

### 5.2 创建任务
**接口地址**: `POST /api/tasks`

**入参**:
```json
{
  "jobId": "1",
  "totalChannels": 3
}
```

**出参**:
```json
{
  "code": 200,
  "message": "任务创建成功",
  "data": {
    "id": "1",
    "jobId": "1",
    "status": "not-started",
    "...": "..."
  }
}
```

### 5.3 更新任务状态
**接口地址**: `PATCH /api/tasks/:id/status`

**入参**:
```json
{
  "status": "in-progress"
}
```

**出参**:
```json
{
  "code": 200,
  "message": "状态更新成功"
}
```

### 5.4 更新任务进度
**接口地址**: `PATCH /api/tasks/:id/progress`

**入参**:
```json
{
  "channelsPublished": 2,
  "resumesViewed": 50,
  "greetingsSent": 25,
  "conversationsActive": 15,
  "resumesRequested": 20,
  "resumesReceived": 10,
  "interviewsScheduled": 5
}
```

**出参**:
```json
{
  "code": 200,
  "message": "进度更新成功"
}
```

---

## 6. 面试管理模块

### 6.1 获取面试列表
**接口地址**: `GET /api/interviews`

**查询参数**:
- `page`: 页码
- `pageSize`: 每页数量
- `status`: 面试状态 (scheduled/completed/cancelled/rescheduled)
- `candidateId`: 候选人ID

**出参**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "list": [
      {
        "id": "1",
        "candidateId": "2",
        "candidateName": "李娜",
        "position": "HR经理",
        "date": "2025-01-15",
        "time": "14:00",
        "interviewer": "王总监",
        "interviewerTitle": "人力资源总监",
        "type": "video",
        "status": "scheduled",
        "location": null,
        "meetingLink": "https://meet.example.com/abc123",
        "notes": "重点考察招聘管理经验"
      }
    ],
    "total": 10,
    "page": 1,
    "pageSize": 10
  }
}
```

### 6.2 创建面试
**接口地址**: `POST /api/interviews`

**入参**:
```json
{
  "candidateId": "2",
  "position": "HR经理",
  "date": "2025-01-15",
  "time": "14:00",
  "interviewer": "王总监",
  "interviewerTitle": "人力资源总监",
  "type": "video",
  "location": null,
  "meetingLink": "https://meet.example.com/abc123",
  "notes": "重点考察招聘管理经验"
}
```

**出参**:
```json
{
  "code": 200,
  "message": "面试创建成功",
  "data": {
    "id": "1",
    "...": "..."
  }
}
```

### 6.3 更新面试
**接口地址**: `PUT /api/interviews/:id`

**入参**: 同创建面试

**出参**:
```json
{
  "code": 200,
  "message": "面试更新成功"
}
```

### 6.4 取消面试
**接口地址**: `PATCH /api/interviews/:id/cancel`

**入参**:
```json
{
  "reason": "候选人时间冲突"
}
```

**出参**:
```json
{
  "code": 200,
  "message": "面试已取消"
}
```

---

## 7. AI聊天模块

### 7.1 获取聊天会话列表
**接口地址**: `GET /api/chat/sessions`

**出参**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "list": [
      {
        "id": "1",
        "title": "招聘咨询 - 前端工程师",
        "createdAt": "2025-01-13T09:00:00Z",
        "updatedAt": "2025-01-13T15:30:00Z"
      }
    ]
  }
}
```

### 7.2 获取聊天历史
**接口地址**: `GET /api/chat/sessions/:id/messages`

**出参**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "messages": [
      {
        "id": "1",
        "role": "assistant",
        "content": "你好！我是AI招聘助手...",
        "timestamp": "2025-01-13T09:00:00Z"
      },
      {
        "id": "2",
        "role": "user",
        "content": "帮我筛选一下前端工程师的简历",
        "timestamp": "2025-01-13T09:01:00Z"
      }
    ]
  }
}
```

### 7.3 发送消息
**接口地址**: `POST /api/chat/sessions/:id/messages`

**入参**:
```json
{
  "content": "帮我筛选一下前端工程师的简历"
}
```

**出参**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "id": "3",
    "role": "assistant",
    "content": "我已经为你筛选了最近的简历...",
    "timestamp": "2025-01-13T09:02:00Z"
  }
}
```

### 7.4 创建新会话
**接口地址**: `POST /api/chat/sessions`

**入参**:
```json
{
  "title": "新对话"
}
```

**出参**:
```json
{
  "code": 200,
  "message": "会话创建成功",
  "data": {
    "id": "2",
    "title": "新对话",
    "createdAt": "2025-01-13T09:00:00Z"
  }
}
```

---

## 8. 账户设置模块

### 8.1 更新个人信息
**接口地址**: `PUT /api/account/profile`

**入参**:
```json
{
  "name": "张三",
  "email": "zhangsan@example.com",
  "role": "hr"
}
```

**出参**:
```json
{
  "code": 200,
  "message": "个人信息更新成功"
}
```

### 8.2 更新密码
**接口地址**: `PUT /api/account/password`

**入参**:
```json
{
  "currentPassword": "oldpassword123",
  "newPassword": "newpassword123"
}
```

**出参**:
```json
{
  "code": 200,
  "message": "密码更新成功"
}
```

### 8.3 上传头像
**接口地址**: `POST /api/account/avatar`

**入参**: FormData (multipart/form-data)
- `file`: 图片文件

**出参**:
```json
{
  "code": 200,
  "message": "头像上传成功",
  "data": {
    "avatarUrl": "https://example.com/avatars/user1.jpg"
  }
}
```

### 8.4 更新通知设置
**接口地址**: `PUT /api/account/notifications`

**入参**:
```json
{
  "emailNotifications": true,
  "taskReminders": true
}
```

**出参**:
```json
{
  "code": 200,
  "message": "通知设置更新成功"
}
```

---

## 9. 统计数据模块

### 9.1 获取Dashboard统计数据
**接口地址**: `GET /api/stats/dashboard`

**出参**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "pendingResumes": 5,
    "upcomingInterviews": 3,
    "activeTasks": 2,
    "openJobs": 10
  }
}
```

### 9.2 获取职位统计数据
**接口地址**: `GET /api/stats/jobs`

**出参**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "totalJobs": 50,
    "activeJobs": 30,
    "totalApplicants": 500,
    "draftJobs": 5
  }
}
```

### 9.3 获取简历统计数据
**接口地址**: `GET /api/stats/resumes`

**出参**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "total": 100,
    "pending": 20,
    "reviewing": 30,
    "interview": 15,
    "offered": 10,
    "rejected": 25
  }
}
```

### 9.4 获取渠道统计数据
**接口地址**: `GET /api/stats/channels`

**出参**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "totalChannels": 5,
    "activeChannels": 4,
    "totalApplicants": 500,
    "averageConversion": 0.23
  }
}
```

### 9.5 获取招聘漏斗数据
**接口地址**: `GET /api/stats/funnel`

**查询参数**:
- `startDate`: 开始日期
- `endDate`: 结束日期

**出参**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "totalResumes": 156,
    "interviewScheduled": 45,
    "offersSent": 12,
    "offersAccepted": 8,
    "conversionRates": {
      "resumeToInterview": 0.288,
      "interviewToOffer": 0.267,
      "offerToAccept": 0.667
    }
  }
}
```

---

## 通用响应格式

### 成功响应
```json
{
  "code": 200,
  "message": "成功",
  "data": {}
}
```

### 错误响应
```json
{
  "code": 400,
  "message": "错误信息",
  "errors": [
    {
      "field": "email",
      "message": "邮箱格式不正确"
    }
  ]
}
```

### HTTP状态码说明
- `200`: 成功
- `201`: 创建成功
- `400`: 请求参数错误
- `401`: 未授权
- `403`: 无权限
- `404`: 资源不存在
- `500`: 服务器错误

---

## 通用查询参数

大部分列表接口支持以下通用查询参数：

- `page`: 页码 (默认: 1)
- `pageSize`: 每页数量 (默认: 10, 最大: 100)
- `sortBy`: 排序字段
- `sortOrder`: 排序方向 (asc/desc)
- `search`: 搜索关键词

## 认证说明

除登录接口外，所有接口都需要在请求头中携带认证token：

```
Authorization: Bearer {token}
```

如果token过期或无效，将返回401错误。

