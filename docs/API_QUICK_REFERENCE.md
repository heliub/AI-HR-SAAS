# AI HR SaaS 系统 - API快速参考

## 🚀 基础信息

- **基础URL**: `http://localhost:8000/api/v1`
- **认证方式**: Bearer Token
- **数据格式**: JSON

## 🔐 认证

```http
Authorization: Bearer YOUR_TOKEN
```

### 登录
```http
POST /auth/login
Content-Type: application/json

{
  "email": "li@demo.com",
  "password": "123456"
}
```

## 👤 用户管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/account/profile` | 获取当前用户信息 |
| PUT | `/account/profile` | 更新用户信息 |

## 💼 职位管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/jobs` | 获取职位列表 |
| GET | `/jobs/{job_id}` | 获取职位详情 |
| POST | `/jobs` | 创建职位 |
| PUT | `/jobs/{job_id}` | 更新职位 |
| DELETE | `/jobs/{job_id}` | 删除职位 |
| PATCH | `/jobs/{job_id}/status` | 更新职位状态 |
| POST | `/jobs/{job_id}/duplicate` | 复制职位 |
| POST | `/jobs/ai-generate` | AI生成职位描述 |

## 📄 简历管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/resumes` | 获取简历列表 |
| GET | `/resumes/{resume_id}` | **获取简历详情** ⭐ |
| PATCH | `/resumes/{resume_id}/status` | 更新简历状态 |
| POST | `/resumes/{resume_id}/ai-match` | AI简历匹配 |
| POST | `/resumes/{resume_id}/send-email` | 发送邮件 |

## 📢 渠道管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/channels` | 获取渠道列表 |
| POST | `/channels` | 创建渠道 |
| PUT | `/channels/{channel_id}` | 更新渠道 |
| DELETE | `/channels/{channel_id}` | 删除渠道 |

## 📋 任务管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/tasks` | 获取任务列表 |
| POST | `/tasks` | 创建任务 |

## 🎯 权限说明

| 角色 | 权限 |
|------|------|
| `admin` | 可查看租户内所有数据 |
| `hr` | 只能查看自己负责的数据 |

## 🧪 测试账号

### 管理员
- **邮箱**: `li@demo.com`
- **密码**: `123456`

### HR
- **邮箱**: `wang@demo.com`
- **密码**: `123456`

## 💡 重要说明

1. **简历详情接口** `/resumes/{resume_id}` 返回完整的关联数据：
   - 工作经历 (`workHistory`)
   - 项目经历 (`projectHistory`)
   - 教育背景 (`educationHistory`)
   - 求职意向 (`jobPreferences`)
   - AI匹配结果 (`aiMatchResults`)
   - 聊天记录 (`chatHistory`)

2. **权限控制**：
   - 管理员可查看所有数据
   - HR只能查看自己创建/负责的数据

3. **字段命名**：
   - API响应使用小驼峰命名 (如 `candidateName`)
   - 数据库使用下划线命名 (如 `candidate_name`)

---

*快速参考文档 - 便于开发时查阅*