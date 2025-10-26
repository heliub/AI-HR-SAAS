# 快速测试指南

## 前置准备

### 1. 启动PostgreSQL测试数据库

选择以下任一方式：

**方式A：使用Docker（推荐）**
```bash
docker run -d \
  --name hr-saas-test-db \
  -e POSTGRES_DB=hr_saas_test \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:15-alpine
```

**方式B：使用本地PostgreSQL**
```bash
# 创建测试数据库
createdb -U postgres hr_saas_test
```

### 2. 验证数据库连接

```bash
# 测试连接
psql -U postgres -d hr_saas_test -c "SELECT version();"
```

## 运行测试

### 方式1：运行所有测试

```bash
cd /Users/zhaopin/work/code/ai/agent/python-ai-hr-saas
uv run pytest tests/ -v
```

### 方式2：运行特定模块测试

```bash
# 认证模块（7个测试）
uv run pytest tests/test_auth.py -v

# 职位管理（11个测试）
uv run pytest tests/test_jobs.py -v

# 简历管理（10个测试）
uv run pytest tests/test_resumes.py -v

# 统计数据（5个测试）
uv run pytest tests/test_stats.py -v

# 账户设置（3个测试）
uv run pytest tests/test_account.py -v
```

### 方式3：运行单个测试

```bash
# 运行特定测试用例
uv run pytest tests/test_auth.py::TestAuth::test_login_success -v
```

## 查看测试覆盖率

```bash
# 生成覆盖率报告
uv run pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# 在浏览器中查看
open htmlcov/index.html
```

## 测试输出说明

### 成功的测试输出
```
tests/test_auth.py::TestAuth::test_login_success PASSED     [ 14%]
tests/test_auth.py::TestAuth::test_get_current_user PASSED  [ 28%]
...
====== 36 passed in 5.23s ======
```

### 如果测试失败
- 查看具体错误信息
- 检查数据库是否正常运行
- 确认API实现与测试预期一致

## 常见问题

### 问题1：数据库连接失败
```
OSError: [Errno 61] Connect call failed
```

**解决方案**：
1. 确认PostgreSQL正在运行：`docker ps` 或 `pg_isready`
2. 检查端口是否正确（默认5432）
3. 验证数据库是否存在：`psql -U postgres -l`

### 问题2：测试数据库不存在
```
FATAL: database "hr_saas_test" does not exist
```

**解决方案**：
```bash
createdb -U postgres hr_saas_test
```

### 问题3：权限问题
```
FATAL: role "postgres" does not exist
```

**解决方案**：
使用正确的用户名和密码，修改 `.env.test` 文件。

## 清理测试环境

```bash
# 停止并删除Docker容器
docker stop hr-saas-test-db
docker rm hr-saas-test-db

# 或删除测试数据库
dropdb -U postgres hr_saas_test
```

## 持续集成示例

可以将测试集成到CI/CD流程：

```bash
# 一键测试脚本
#!/bin/bash
set -e

# 启动测试数据库
docker run -d --name test-db \
  -e POSTGRES_DB=hr_saas_test \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:15-alpine

# 等待数据库就绪
sleep 5

# 运行测试
uv run pytest tests/ -v --cov=app

# 清理
docker stop test-db
docker rm test-db
```

