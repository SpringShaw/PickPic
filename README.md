# 去留 - 相册整理工具

> 📷 1:1 复刻 iOS 热门独立 APP《去留》的算法、手势、UI 视觉、交互逻辑  
> 纯本地运行，无外网请求，无数据收集，所有数据保存在本地

## ✨ 功能特性

- **随机推送**：全局打乱图片，跨文件夹、跨时间、跨地点随机推送
- **手势操作**：
  - 右滑 → 保留，切换下一张
  - 上滑 → 移入回收站（二次确认）
  - 双击 → 收藏，触发动画
  - 单击 → 查看图片详情（时间、地点、路径）
- **左滑找回**：找回上一张右滑跳过的照片
- **智能屏蔽**：已浏览图片自动加入黑名单，默认 3 年不再推送
- **去重过滤**：可选开启重复图片自动过滤
- **数据统计**：实时展示已浏览、已收藏、已清理空间
- **iOS 极简风**：纯白背景、大面积留白、轻量动画
- **目录可配**：首次部署后在设置页面配置图片/收藏/回收站目录
- **视频支持**：视频文件缩略图展示 + 播放

## 🎨 设计规范

### 配色

| 元素 | 颜色 |
|------|------|
| 页面背景 | `#FFFFFF` 纯白 |
| 主要文字 | `#333333` 深灰 |
| 辅助提示文字 | `#888888` 浅灰 |
| 收藏爱心 | `#FFB6C1` 淡粉色 |
| 弹窗底色 | `#F8F8F8` 浅灰白 |

### 交互动画（轻量化，低性能消耗）

| 手势 | 动效 |
|------|------|
| 上滑删除 | 图片向上滑出 + 淡出 |
| 右滑保留 | 图片向右平滑滑出 |
| 左滑找回 | 图片从小到大召回动画 |
| 双击收藏 | 图片中心淡粉色爱心闪烁反馈 |
| 弹窗 | iOS 风格圆角极简弹窗 |

### UI 组件风格

- 信息条、按钮等浮层组件使用白色半透明背景 `rgba(255, 255, 255, 0.92)` + `backdrop-filter: blur(12px)`
- 细微阴影 `box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06)`
- 圆角统一 12px
- 不使用深色/黑色半透明背景（与整体纯白风格冲突）

## 📦 项目结构

```
photo-sorter/
├── frontend/                # 前端（Vue3 + Vite + TailwindCSS）
│   ├── src/
│   │   ├── App.vue          # 主页面
│   │   ├── components/
│   │   │   ├── PhotoCard.vue      # 图片卡片（手势交互）
│   │   │   ├── PhotoInfoBar.vue   # 照片信息条
│   │   │   ├── StatsBar.vue       # 顶部统计栏
│   │   │   ├── ImageViewer.vue    # 全屏查看器
│   │   │   ├── InfoPanel.vue      # 图片信息弹窗
│   │   │   ├── ConfirmDialog.vue  # 确认弹窗
│   │   │   ├── SettingsPanel.vue  # 设置面板
│   │   │   ├── RecyclePanel.vue   # 回收站管理
│   │   │   └── FavoritesPanel.vue # 收藏夹管理
│   │   └── services/api.js
│   └── 构建配置
├── backend/                 # 后端（Python3 + FastAPI）
│   ├── app/
│   │   ├── main.py          # FastAPI 入口
│   │   ├── config.py        # 配置项
│   │   ├── models/database.py
│   │   ├── api/routes.py
│   │   └── services/photo_service.py
│   └── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── deploy.sh                # 一键部署脚本
├── .env.example             # 环境变量模板
├── LICENSE
├── ROADMAP.md
└── README.md
```

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/SpringShaw/Photo-Sorter.git
cd Photo-Sorter

# 2. 配置
cp .env.example .env
vim .env
# 修改 PHOTOS_DIR、FAVORITES_DIR、RECYCLE_DIR 为你的实际路径

# 3. 一键部署
chmod +x deploy.sh
./deploy.sh

# 4. 访问
# 浏览器打开 http://localhost:8082
```

### 方式二：Docker Compose 手动部署

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 配置目录路径

# 2. 创建数据目录
mkdir -p data/db data/thumbnails

# 3. 构建并启动
docker compose up -d --build

# 4. 访问 http://localhost:8082
```

### 方式三：本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8082

# 前端（开发模式）
cd frontend
npm install
npm run dev
```

## 🔧 配置说明

### 环境变量（.env）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | `8082` | 访问端口 |
| `PHOTOS_DIR` | `./photos` | 图片源目录（宿主机路径） |
| `FAVORITES_DIR` | `./favorites` | 收藏目录 |
| `RECYCLE_DIR` | `./recycle` | 回收站目录 |
| `BLACKLIST_DURATION` | `3y` | 黑名单时长：`1y` / `3y` / `forever` |
| `ENABLE_DUPLICATE_FILTER` | `true` | 重复图片过滤 |

### 目录挂载说明

docker-compose.yml 中的卷映射：

| 容器路径 | 宿主机路径 | 说明 |
|----------|-----------|------|
| `/photos` | `.env` 中 `PHOTOS_DIR` | 图片源目录（只读） |
| `/favorites` | `.env` 中 `FAVORITES_DIR` | 收藏目录 |
| `/recycle` | `.env` 中 `RECYCLE_DIR` | 回收站目录 |
| `/app/db` | `./data/db` | SQLite 数据库 |
| `/app/data/thumbnails` | `./data/thumbnails` | 缩略图缓存 |

### 设置页面

首次打开后，点击左下角 ⚙️ 齿轮进入设置页面，可配置：

- 图片源目录路径
- 收藏目录路径
- 回收站目录路径
- 黑名单时长
- 重复过滤开关

## 📱 使用说明

| 手势 | 操作 |
|------|------|
| 右滑 | 保留照片，切换下一张 |
| 上滑 | 删除照片（移入回收站，可撤销） |
| 左滑 | 找回上一张跳过的照片 |
| 双击 | 收藏照片 |
| 单击 | 查看图片信息 |
| 放大查看按钮 | 全屏查看，支持双指缩放/拖动 |

## 🛠️ 技术栈

- **前端**：Vue3 + Vite + TailwindCSS
- **后端**：Python3 + FastAPI + SQLite
- **容器**：Docker + python:3.11-slim
- **图片处理**：Pillow + pillow-heif（HEIC 支持）
- **视频处理**：ffmpeg（缩略图 + 元数据）

## 📋 支持的格式

| 类型 | 格式 |
|------|------|
| 图片 | JPG, JPEG, PNG, WebP, HEIC, HEIF, BMP, GIF, TIFF |
| 视频 | MP4, MOV, AVI, MKV, WebM, 3GP, FLV |

## 📄 许可证

[MIT License](LICENSE) - 纯本地私有化运行，无任何外网依赖。

## 🙏 致谢

灵感来源：iOS 独立 APP《去留》
