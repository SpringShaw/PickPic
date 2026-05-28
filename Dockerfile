FROM python:3.10-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8082 \
    DB_DIR=/app/db \
    NAS_HOST_DIR=/nas/host

# 安装系统依赖（HEIC支持）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libheif-dev \
    libde265-dev \
    libx265-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装 Node.js 20（用于构建前端）
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先复制后端依赖安装
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 复制前端代码并构建
COPY frontend/ /app/frontend/
RUN cd /app/frontend && \
    npm install && \
    npm run build && \
    rm -rf /app/frontend/node_modules /app/frontend/src

# 复制后端代码
COPY backend/ /app/backend/

# 确保目录存在
RUN mkdir -p /nas/host /app/db

# 暴露端口
EXPOSE 8082

# 启动服务
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8082"]
