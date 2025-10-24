# AI-Powered HR Recruitment SAAS Platform

一个基于AI大模型的智能招聘SAAS系统，帮助HR高效管理招聘流程。

## 功能特性

- 🤖 **AI对话**: 通过自然语言对话完成招聘全流程操作
- 👥 **多租户**: 支持企业级多租户架构
- 📊 **职位管理**: 完整的职位信息管理和发布
- 📄 **简历管理**: 智能简历解析和结构化存储
- 🎯 **人岗匹配**: 基于AI的智能人岗匹配
- 🔗 **平台集成**: LinkedIn、Jobstreet等平台自动化集成
- 📧 **邮件收集**: 自动收集和处理简历邮件
- 💬 **智能撮合**: AI驱动的候选人沟通
- 🌐 **多语言**: 支持中文、英文、印尼语

## 技术栈

- **框架**: FastAPI 0.115+
- **数据库**: PostgreSQL 16+ with asyncpg
- **缓存**: Redis 7+
- **任务队列**: Celery 5.4+
- **AI**: LangChain + Multi-Model Support
- **RPA**: Playwright
- **可观测性**: OpenTelemetry + Jaeger + Prometheus
- **部署**: Docker + Docker Compose

## 快速开始

### 环境要求

- Python 3.11+
- Docker & Docker Compose
- uv

### 安装依赖

```bash
# 安装uv（如果未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖
uv sync

# 安装开发依赖
uv sync --extra dev

# 安装Playwright浏览器
uv run playwright install chromium
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件，配置数据库、Redis、AI API Key等
```

### 数据库迁移

```bash
# 初始化数据库
uv run alembic upgrade head
```

### 启动服务

#### 开发环境

```bash
# 启动API服务
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动Celery Worker（新终端）
uv run celery -A app.tasks.celery_app worker --loglevel=info

# 启动Celery Beat（新终端）
uv run celery -A app.tasks.celery_app beat --loglevel=info
```

#### 生产环境（Docker）

```bash
# 启动所有服务
docker-compose -f docker/docker-compose.yml up -d

# 查看日志
docker-compose -f docker/docker-compose.yml logs -f

# 停止服务
docker-compose -f docker/docker-compose.yml down
```

## 项目结构

```
python-ai-hr-saas/
├── app/                      # 应用主目录
│   ├── api/                 # API路由层
│   ├── models/              # 数据库模型
│   ├── schemas/             # Pydantic Schema
│   ├── services/            # 业务逻辑层
│   ├── ai/                  # AI模块
│   ├── integrations/        # 三方平台集成
│   ├── rpa/                 # RPA模块
│   ├── tasks/               # Celery任务
│   ├── infrastructure/      # 基础设施
│   ├── observability/       # 可观测性
│   ├── middleware/          # 中间件
│   ├── core/                # 核心配置
│   └── main.py              # 应用入口
├── migrations/              # 数据库迁移
├── tests/                   # 测试
├── docker/                  # Docker配置
├── scripts/                 # 脚本
└── configs/                 # 配置文件
```

## API文档

启动服务后访问：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 监控面板

- Jaeger UI: http://localhost:16686
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- MinIO Console: http://localhost:9001

## 开发指南

### 代码风格

```bash
# 格式化代码
uv run black app/

# 代码检查
uv run ruff check app/

# 类型检查
uv run mypy app/
```

### 测试

```bash
# 运行所有测试
uv run pytest

# 运行测试并生成覆盖率报告
uv run pytest --cov=app --cov-report=html
```

## 许可证

[MIT License](LICENSE)
