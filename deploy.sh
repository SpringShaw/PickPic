#!/bin/bash
set -e

cd "$(dirname "$0")"

# 检查 .env
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "⚠️  已从 .env.example 创建 .env，请编辑配置："
        echo "   vim .env"
        echo ""
        echo "   必须修改："
        echo "   - PHOTOS_DIR  （图片目录）"
        echo "   - FAVORITES_DIR （收藏目录）"
        echo "   - RECYCLE_DIR  （回收站目录）"
        echo ""
        exit 1
    else
        echo "❌ 缺少 .env 文件，请创建或复制 .env.example"
        exit 1
    fi
fi

# 创建数据目录
mkdir -p data/db data/thumbnails

# 构建并启动
echo "🔨 构建镜像..."
docker compose build

echo "🚀 启动服务..."
docker compose up -d

echo ""
echo "✅ PickPic 已启动"
echo "   访问: http://localhost:${PORT:-8082}"
echo "   健康检查: curl http://localhost:${PORT:-8082}/api/stats"
