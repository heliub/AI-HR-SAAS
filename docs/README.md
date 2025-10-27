# AI HR SaaS 系统 - API文档目录

## 📚 文档说明

本目录包含AI HR SaaS系统的完整API文档和相关资源。

## 📄 文档列表

### 1. 完整API参考文档
**文件**: `COMPLETE_API_REFERENCE.md`

- **说明**: 最完整的API接口文档，包含所有接口的详细说明
- **内容**:
  - 认证说明
  - 用户管理
  - 职位管理（CRUD + AI生成）
  - 简历管理（完整关联数据）
  - 渠道管理
  - 任务管理
  - 错误处理
  - 数据字典
- **适用**: 开发人员完整参考

### 2. 快速参考文档
**文件**: `API_QUICK_REFERENCE.md`

- **说明**: 简化的API快速参考，便于开发时快速查阅
- **内容**:
  - 接口列表表格
  - 基础请求示例
  - 权限说明
  - 测试账号
- **适用**: 日常开发快速查阅

### 3. 原始API文档
**文件**: `API_DOCUMENTATION.md`

- **说明**: 原始版本的API文档（可能不是最新的）
- **状态**: 仅供参考，建议使用上面的新文档

### 4. Postman集合
**文件**: `postman_collection.json`

- **说明**: 可直接导入Postman的API集合
- **内容**:
  - 所有主要接口
  - 预设请求示例
  - 自动化脚本（登录后自动保存token）
- **使用方法**:
  1. 打开Postman
  2. 点击Import
  3. 选择File标签
  4. 上传`postman_collection.json`文件

### 5. 数据库模式
**文件**: `DATABASE_SCHEMA.sql`

- **说明**: 完整的数据库表结构定义
- **内容**: 所有表结构、字段定义、注释

### 6. 字段映射文档
**文件**: `FIELD_MAPPING.md`

- **说明**: 数据库字段与API字段的映射关系
- **内容**: 下划线命名与小驼峰命名的对应关系

### 7. 模拟数据
**文件**: `mock-data.ts`

- **说明**: TypeScript格式的模拟数据
- **内容**: 各个模块的示例数据

## 🚀 快速开始

### 1. 登录获取Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "li@demo.com",
       "password": "123456"
     }'
```

### 2. 使用Token调用API
```bash
curl -X GET "http://localhost:8000/api/v1/resumes/40000000-0000-0000-0000-000000000001" \
     -H "Authorization: Bearer YOUR_TOKEN"
```

## 🧪 测试账号

| 角色 | 邮箱 | 密码 | 权限 |
|------|------|------|------|
| 管理员 | `li@demo.com` | `123456` | 查看所有数据 |
| HR | `wang@demo.com` | `123456` | 查看自己负责的数据 |

## ⭐ 核心接口

### 简历详情接口（推荐测试）
```
GET /api/v1/resumes/{resume_id}
```
- 返回完整的简历信息，包括：
  - 工作经历
  - 项目经历
  - 教育背景
  - 求职意向
  - AI匹配结果
  - 聊天记录

### AI生成职位描述
```
POST /api/v1/jobs/ai-generate
```
- 智能生成职位描述和要求

## 🔧 开发提示

### 权限控制
- 管理员(`admin`): 可查看租户内所有数据
- HR(`hr`): 只能查看自己负责的数据

### 字段命名规范
- API响应: 小驼峰命名 (`candidateName`)
- 数据库: 下划线命名 (`candidate_name`)

### 关键功能
1. **简历详情**: 包含完整的关联数据
2. **AI匹配**: 智能分析简历与职位的匹配度
3. **权限控制**: 基于角色的数据访问控制

## 📞 支持

如有问题，请参考：
1. `COMPLETE_API_REFERENCE.md` - 完整API文档
2. `API_QUICK_REFERENCE.md` - 快速参考
3. `postman_collection.json` - 导入Postman测试

---

*文档更新时间: 2025-01-27*