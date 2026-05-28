FROM python:3.11-slim

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

WORKDIR /app/backend

# 复制后端依赖安装
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ .

# 确保目录存在
RUN mkdir -p /nas/host /app/db

# 暴露端口
EXPOSE 8082

# 启动服务
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082"]
