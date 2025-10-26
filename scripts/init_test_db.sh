#!/bin/bash

# 初始化测试数据库脚本

set -e

echo "正在创建测试数据库..."

# 获取数据库配置
DB_HOST="${TEST_DB_HOST:-localhost}"
DB_PORT="${TEST_DB_PORT:-55000}"
DB_USER="${TEST_DB_USER:-postgres}"
DB_PASSWORD="${TEST_DB_PASSWORD:-postgrespw}"
DB_NAME="${TEST_DB_NAME:-hr_saas_test}"

# 检查 PostgreSQL 是否运行
if ! docker ps | grep -q postgres; then
    echo "错误: PostgreSQL 容器未运行"
    echo "请先启动 PostgreSQL: cd docker && docker-compose up -d postgres"
    exit 1
fi

# 创建测试数据库（如果不存在）
echo "创建数据库: $DB_NAME"
docker exec -it $(docker ps -qf "name=postgres") psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;" || true
docker exec -it $(docker ps -qf "name=postgres") psql -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;"

echo "✅ 测试数据库创建成功: $DB_NAME"
echo ""
echo "现在可以运行测试了:"
echo "  pytest tests/"
echo ""
echo "保留测试数据用于调试:"
echo "  KEEP_TEST_DATA=1 pytest tests/"

