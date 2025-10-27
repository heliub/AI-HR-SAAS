#!/bin/bash

# 🚀 生产环境优化服务部署脚本
# 使用方法: ./deploy_optimized_services.sh

set -e  # 遇到错误立即退出

echo "🚀 开始部署生产优化服务..."

# 检查当前目录
if [ ! -f "app/services/base_service.py" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 备份当前代码
echo "📦 备份当前服务文件..."
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
cp app/services/*.py backups/$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true

# 安装必要的依赖
echo "📦 安装优化依赖..."
pip install redis structlog prometheus-client

# 部署优化的服务
echo "🔧 部署优化的服务文件..."

# 1. 部署优化的简历服务
if [ -f "app/services/resume_service_optimized.py" ]; then
    echo "✅ 部署优化简历服务..."
    cp app/services/resume_service_optimized.py app/services/resume_service.py
fi

# 2. 部署安全基础服务
if [ -f "app/services/secure_base_service.py" ]; then
    echo "✅ 部署安全基础服务..."
    cp app/services/secure_base_service.py app/services/base_service.py
fi

# 3. 部署缓存服务
if [ -f "app/services/cache_service.py" ]; then
    echo "✅ 部署缓存服务..."
    echo "缓存服务已就绪，请确保Redis正在运行"
fi

# 创建环境配置文件
echo "📝 创建环境配置..."
cat > .env.optimized << EOF
# 生产优化环境配置
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
CACHE_TTL_DEFAULT=3600
CACHE_TTL_SENSITIVE=1800

# 性能监控
ENABLE_METRICS=true
METRICS_PORT=8001

# 安全配置
ENABLE_PERMISSION_CHECK=true
TENANT_ISOLATION=true
EOF

# 更新requirements.txt
echo "📦 更新依赖列表..."
echo "redis>=4.5.0" >> requirements.txt
echo "structlog>=23.1.0" >> requirements.txt
echo "prometheus-client>=0.17.0" >> requirements.txt

# 创建Docker Compose配置
echo "🐳 创建Docker配置..."
cat > docker-compose.optimized.yml << EOF
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:password@postgres:5432/dbname
    depends_on:
      - redis
      - postgres
    volumes:
      - .:/app

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: hr_saaS
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  redis_data:
  postgres_data:
  grafana_data:
EOF

# 创建Prometheus配置
mkdir -p monitoring
cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'hr-saas-app'
    static_configs:
      - targets: ['app:8001']
    metrics_path: '/metrics'
EOF

# 运行语法检查
echo "🔍 检查Python语法..."
python -m py_compile app/services/*.py || {
    echo "❌ 语法检查失败，请检查代码"
    exit 1
}

# 运行基础测试
echo "🧪 运行基础测试..."
python -c "
import asyncio
from app.services.resume_service_optimized import OptimizedResumeService
print('✅ 优化服务导入成功')
" || {
    echo "❌ 服务测试失败"
    exit 1
}

echo ""
echo "🎉 部署完成！"
echo ""
echo "📋 下一步操作："
echo "1. 启动Redis: docker run -d -p 6379:6379 redis:7-alpine"
echo "2. 设置环境变量: export REDIS_URL='redis://localhost:6379/0'"
echo "3. 启动应用: uvicorn app.main:app --reload"
echo "4. 检查健康状态: curl http://localhost:8000/api/v1/resumes/health"
echo ""
echo "📊 性能监控："
echo "- Prometheus: http://localhost:9090"
echo "- Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "📚 更多信息请查看:"
echo "- PRODUCTION_RESTRUCTURE_PLAN.md"
echo "- app/services/resume_service_optimized.py"
echo "- app/services/secure_base_service.py"
echo ""

# 询问是否启动服务
read -p "是否现在启动优化服务？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 启动服务..."
    if command -v docker &> /dev/null; then
        echo "使用Docker启动服务..."
        docker-compose -f docker-compose.optimized.yml up -d
    else
        echo "请手动启动Redis和应用服务"
        echo "Redis: docker run -d -p 6379:6379 redis:7-alpine"
        echo "应用: uvicorn app.main:app --reload"
    fi
fi

echo "✅ 部署脚本执行完成！"