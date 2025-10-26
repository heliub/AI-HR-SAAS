# 测试文档

## 测试概述

本项目包含完整的API接口单元测试，覆盖以下模块：
- 认证模块（7个测试用例）
- 职位管理（11个测试用例）
- 简历管理（10个测试用例）
- 统计数据（5个测试用例）
- 账户设置（3个测试用例）

**总计：36个测试用例**

## 测试环境要求

### 数据库要求

本项目使用PostgreSQL作为生产数据库，数据模型中使用了PostgreSQL特有的数据类型（如ARRAY、JSONB、UUID等）。因此，**测试必须使用PostgreSQL数据库**，不支持SQLite。

### 启动测试数据库

#### 方法1：使用Docker（推荐）

```bash
# 启动PostgreSQL测试数据库
docker run -d \\
  --name hr-saas-test-db \\
  -e POSTGRES_DB=hr_saas_test \\
  -e POSTGRES_USER=postgres \\
  -e POSTGRES_PASSWORD=postgres \\
  -p 5432:5432 \\
  postgres:15-alpine
```

#### 方法2：使用本地PostgreSQL

如果已安装PostgreSQL，创建测试数据库：

```bash
# 登录PostgreSQL
psql -U postgres

# 创建测试数据库
CREATE DATABASE hr_saas_test;
\q
```

## 运行测试

### 1. 配置环境变量

创建 `.env.test` 文件（已提供模板）：

```bash
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/hr_saas_test
SECRET_KEY=test-secret-key-for-testing-only
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24
```

**注意**：如果PostgreSQL运行在其他端口或主机，请相应修改 `TEST_DATABASE_URL`。

### 2. 运行所有测试

```bash
# 使用uv运行测试
uv run pytest tests/ -v

# 或使用测试脚本
bash scripts/run_tests.sh
```

### 3. 运行特定模块测试

```bash
# 测试认证模块
uv run pytest tests/test_auth.py -v

# 测试职位管理模块
uv run pytest tests/test_jobs.py -v

# 测试简历管理模块
uv run pytest tests/test_resumes.py -v

# 测试统计模块
uv run pytest tests/test_stats.py -v

# 测试账户设置模块
uv run pytest tests/test_account.py -v
```

### 4. 查看测试覆盖率

```bash
# 生成覆盖率报告
uv run pytest tests/ --cov=app --cov-report=html --cov-report=term

# 在浏览器中查看详细报告
open htmlcov/index.html
```

## 测试结构

```
tests/
├── __init__.py          # 测试包初始化
├── conftest.py          # Pytest配置和fixtures
├── test_auth.py         # 认证模块测试
├── test_jobs.py         # 职位管理测试
├── test_resumes.py      # 简历管理测试
├── test_stats.py        # 统计数据测试
├── test_account.py      # 账户设置测试
└── README.md            # 本文档
```

## Fixtures说明

### 数据库Fixtures
- `engine`: 测试数据库引擎（session级别）
- `db_session`: 数据库会话（每个测试独立）

### HTTP客户端Fixtures
- `client`: 异步HTTP测试客户端

### 测试数据Fixtures
- `test_tenant`: 测试租户
- `test_user`: 测试用户
- `test_job`: 测试职位
- `test_resume`: 测试简历

### 认证Fixtures
- `auth_token`: JWT认证Token
- `auth_headers`: 包含认证Token的请求头

## 编写新测试

### 示例：添加新的测试用例

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestMyFeature:
    async def test_my_endpoint(self, client: AsyncClient, auth_headers: dict):
        """测试我的接口"""
        response = await client.get(
            "/api/v1/my-endpoint",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
```

## 持续集成

测试可以集成到CI/CD流程中：

```yaml
# .github/workflows/test.yml 示例
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: hr_saas_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install uv
      - run: uv sync --all-extras
      - run: uv run pytest tests/ -v
```

## 故障排除

### 问题1：数据库连接失败

```
OSError: Multiple exceptions: [Errno 61] Connect call failed
```

**解决方案**：确保PostgreSQL数据库正在运行，检查连接信息是否正确。

### 问题2：ARRAY类型编译错误

```
sqlalchemy.exc.CompileError: Compiler can't render element of type ARRAY
```

**解决方案**：这是因为使用了SQLite测试数据库。请切换到PostgreSQL数据库。

### 问题3：表不存在

**解决方案**：测试会自动创建表结构。如果遇到问题，手动删除测试数据库并重新运行测试。

## 最佳实践

1. **隔离测试**：每个测试应该独立运行，不依赖其他测试的结果
2. **清理数据**：测试后自动回滚数据库事务，保持数据库清洁
3. **Mock外部服务**：对于第三方API调用，使用Mock避免真实调用
4. **测试命名**：使用描述性的测试函数名，如`test_login_with_invalid_password`
5. **断言清晰**：使用明确的断言消息，便于定位问题

## 参考资料

- [Pytest文档](https://docs.pytest.org/)
- [Pytest-asyncio文档](https://pytest-asyncio.readthedocs.io/)
- [HTTPX文档](https://www.python-httpx.org/)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)

