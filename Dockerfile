FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8082 \
    DB_DIR=/app/db \
    NAS_HOST_DIR=/nas/host

# 安装系统依赖（HEIC支持 + 视频处理）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libheif-dev \
    libde265-dev \
    libx265-dev \
    build-essential \
    ffmpeg

WORKDIR /app/backend

# 复制后端依赖安装
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 移除编译工具，减小镜像体积
RUN apt-get remove -y build-essential && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# 复制后端代码
COPY backend/ .

# 确保目录存在
RUN mkdir -p /photos /favorites /recycle /app/db /app/data/thumbnails

# 暴露端口
EXPOSE 8082

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /photos /favorites /recycle /app/db /app/data
USER appuser

# 启动服务
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082"]
