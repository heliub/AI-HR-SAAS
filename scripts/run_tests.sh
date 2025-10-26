#!/bin/bash

# 运行自动化测试脚本

set -e

echo "========================================="
echo "开始运行测试"
echo "========================================="

# 加载测试环境变量
if [ -f .env.test ]; then
    export $(cat .env.test | grep -v '^#' | xargs)
fi

# 检查测试数据库是否存在，不存在则创建
echo "检查测试数据库..."
PGPASSWORD=${POSTGRES_PASSWORD:-postgres} psql -h ${POSTGRES_HOST:-localhost} -U ${POSTGRES_USER:-postgres} -lqt | cut -d \| -f 1 | grep -qw hr_saas_test || {
    echo "创建测试数据库..."
    PGPASSWORD=${POSTGRES_PASSWORD:-postgres} psql -h ${POSTGRES_HOST:-localhost} -U ${POSTGRES_USER:-postgres} -c "CREATE DATABASE hr_saas_test;"
}

# 运行测试
echo "运行单元测试..."
pytest tests/ -v --tb=short --cov=app --cov-report=term-missing --cov-report=html

echo ""
echo "========================================="
echo "测试完成！"
echo "========================================="
echo ""
echo "测试覆盖率报告已生成到 htmlcov/ 目录"
echo "可以通过浏览器打开 htmlcov/index.html 查看详细报告"

