# 去留 — 相册整理工具

[English](./README.en.md) | **简体中文**

> 1:1 复刻 iOS 热门独立 APP《去留》的 Web 版相册整理工具。Tinder 式卡片交互，快决策照片去留。**纯本地运行、无外网请求、无数据收集**，集成随机推送、手势操作（右滑/上滑/双击/左滑找回）、智能黑名单、MD5 去重过滤、缩略图缓存、视频播放、全屏查看、回收站管理、收藏夹、EXIF 解析等全部功能。

## 界面预览

> 截图待补充，请将中文界面截图放入 `README.assets/` 目录。

## 功能特性

### 📷 随机推送
- 全局打乱图片，跨文件夹、跨时间、跨地点随机推送
- 照片/视频双模式切换，互不干扰
- 双层卡片架构：当前照片 + 下一张预加载，滑动时背面卡片渐进揭示

### ✋ 手势操作
- **右滑** → 保留照片，切换下一张
- **上滑** → 移入回收站（二次确认，可撤销）
- **双击** → 收藏照片，触发淡粉色爱心动画
- **单击** → 查看照片详情（时间、地点、路径、分辨率）
- PC 端鼠标拖拽完全兼容

### ↩️ 左滑找回
- 找回上一张右滑跳过的照片
- 带 ease-out 缩放动画（0.3 → 1.0），视觉流畅

### 🚫 智能屏蔽
- 已浏览图片自动加入黑名单，默认 3 年不重复推送
- 支持 1 年 / 3 年 / 永久 三档可调
- 后台增量扫描，新增/删除照片自动感知

### 🔄 去重过滤
- 预计算 MD5 哈希，基于内容指纹自动过滤重复图片
- 相同照片只推送一次，可选开关

### 🎬 视频支持
- 7 种视频格式：MP4、MOV、AVI、MKV、WebM、3GP、FLV
- ffmpeg 提取第一帧做缩略图，ffprobe 读取时长/分辨率
- 全屏查看器内置 `<video>` 播放控件

### 🔍 全屏查看
- 单击「放大查看」按钮进入全屏模式
- 支持双指缩放（0.5x ~ 5x）、双击放大/还原、拖动平移
- 鼠标滚轮缩放（PC 端）

### 🗑️ 回收站管理
- 删除的照片移入回收站，非直接删除
- 支持单张恢复、批量恢复、全部恢复
- 支持选中永久删除、全部清空（二次确认）
- 回收站缩略图自动补生成

### ⭐ 收藏夹
- 双击收藏的照片集中浏览
- 支持取消收藏、移入回收站
- 收藏文件自动复制到独立目录

### 📊 数据统计
- 实时展示已浏览、已收藏、已清理（释放空间 MB）
- 支持重置黑名单、重置统计数据

### ⚙️ 灵活配置
- 首次部署后在设置页面配置图片源/收藏/回收站目录
- 目录路径实时验证（检查是否存在、可写、图片数量）
- 手动触发全量重新扫描

### 🖼️ 性能优化
- 400×400 JPEG 缩略图缓存，加载速度 10x+
- EXIF Orientation 自动方向修正
- 33K+ 照片秒级随机推送（SQLite 缓存）
- 扫描期间不阻塞正常浏览

### 🎨 iOS 极简设计
- 纯白背景 `#FFFFFF`，大面积留白
- 毛玻璃效果：`rgba(255,255,255,0.92)` + `backdrop-filter: blur(12px)`
- 轻量动画：弹出/滑出/缩放/淡入淡出
- 淡粉色收藏爱心 `#FFB6C1`
- 移动端 + PC 端响应式适配

## 📦 项目结构

```
Photo-Sorter/
├── frontend/                # Vue3 + Vite + TailwindCSS
│   └── src/
│       ├── App.vue          # 主页面（双层卡片架构）
│       ├── components/      # 9 个组件
│       ├── services/api.js  # API 封装（15 个接口）
│       └── utils/           # 共享工具函数
├── backend/                 # Python3 + FastAPI + SQLite
│   └── app/
│       ├── main.py          # FastAPI 入口
│       ├── config.py        # 配置项
│       ├── models/          # 数据库模型
│       ├── api/routes.py    # 19 个 REST API
│       └── services/        # 核心业务逻辑
├── Dockerfile
├── docker-compose.yml
├── deploy.sh                # 一键部署脚本
├── ROADMAP.md               # 开发计划
└── LICENSE                  # MIT
```

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
git clone https://github.com/SpringShaw/Photo-Sorter.git
cd Photo-Sorter
cp .env.example .env
# 编辑 .env 配置 PHOTOS_DIR、FAVORITES_DIR、RECYCLE_DIR
chmod +x deploy.sh
./deploy.sh
# 浏览器打开 http://localhost:8082
```

### 方式二：Docker Compose

```bash
cp .env.example .env
mkdir -p data/db data/thumbnails
docker compose up -d --build
# 访问 http://localhost:8082
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

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | `8082` | 访问端口 |
| `PHOTOS_DIR` | `./photos` | 图片源目录（宿主机路径） |
| `FAVORITES_DIR` | `./favorites` | 收藏目录 |
| `RECYCLE_DIR` | `./recycle` | 回收站目录 |
| `BLACKLIST_DURATION` | `3y` | 黑名单时长：`1y` / `3y` / `forever` |
| `ENABLE_DUPLICATE_FILTER` | `true` | 重复图片过滤 |

## 📱 手势速查

| 手势 | 操作 |
|------|------|
| 右滑 | 保留照片，下一张 |
| 上滑 | 删除照片（回收站） |
| 左滑 | 找回上一张 |
| 双击 | 收藏 |
| 单击 | 查看信息 |

## 🛠️ 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + TailwindCSS |
| 后端 | Python 3 + FastAPI + SQLite |
| 容器 | Docker + python:3.11-slim |
| 图片处理 | Pillow + pillow-heif（HEIC） |
| 视频处理 | ffmpeg（缩略图 + 元数据） |

## 📋 支持格式

| 类型 | 格式 |
|------|------|
| 图片 | JPG, JPEG, PNG, WebP, HEIC, HEIF, BMP, GIF, TIFF |
| 视频 | MP4, MOV, AVI, MKV, WebM, 3GP, FLV |

## 版本历史

查看 [ROADMAP.md](./ROADMAP.md) 了解已完成功能和开发计划。

## 特点

- 🔒 纯本地运行，无外网请求，数据完全私有
- 🐳 Docker 一键部署，5 分钟上手
- 📱 移动端 + PC 端手势全面适配
- ⚡ 33K+ 照片秒级随机推送
- 🎨 iOS 极简风格，轻量动画
- 🆓 MIT 开源协议

## 许可证

[MIT License](LICENSE)

## 致谢

灵感来源：iOS 独立 APP《去留》
