# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy project configuration files
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using uv
# --frozen: Sync with uv.lock
# --no-install-project: Only install dependencies, not the project itself yet (for caching)
# --no-dev: Do not install dev dependencies
RUN uv sync --frozen --no-install-project --no-dev

# Copy the rest of the application code
COPY . .

# Install the project itself
RUN uv sync --frozen --no-dev

# DATABASE_URL placeholder
# 生产环境建议通过 Google Secret Manager 注入，而不是写在这里
ENV DATABASE_URL="postgresql://hr_saas:hr_saas_7f59c26c_\$@/hr_saas?host=/cloudsql/recruiterai-479514:us-west2:recruiterai"

# Default port for Cloud Run
ENV PORT=8080

# Expose the port
EXPOSE 8080

# Gunicorn workers configuration
# Cloud Run 默认提供 1 vCPU，Python 存在 GIL 锁，单核情况下增加 worker 不会提升性能反而增加开销。
# FastAPI 是异步框架，单 worker 即可处理高并发 I/O。
# 如果您在 Cloud Run 配置了 >1 vCPU，可以通过环境变量 WORKERS 调整此值。
ENV WORKERS=1

# Use Gunicorn with Uvicorn workers for production
# --bind: 监听 0.0.0.0:$PORT
CMD ["sh", "-c", "uv run gunicorn app.main:app --workers $WORKERS --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT"]
