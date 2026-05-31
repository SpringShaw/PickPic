# 去留 - NAS 相册整理工具

> 📷 1:1 复刻 iOS 热门独立 APP《去留》的算法、手势、UI 视觉、交互逻辑  
> 纯本地运行，无外网请求，无数据收集，所有数据保存在 NAS 宿主机内

## ✨ 功能特性

- **随机推送**：全局打乱图片，跨文件夹、跨时间、跨地点随机推送
- **手势操作**：
  - 右滑 → 保留，切换下一张
  - 上滑 → 移入回收站（二次确认）
  - 双击 → 收藏，触发动画
  - 单击 → 查看图片详情（时间、地点、路径）
- **智能屏蔽**：已浏览图片自动加入黑名单，默认 3 年不再推送
- **去重过滤**：可选开启重复图片自动过滤
- **数据统计**：实时展示已浏览、已收藏、已清理空间
- **iOS 极简风**：纯白背景、大面积留白、轻量动画
- **目录可配**：首次部署后在设置页面配置图片/收藏/回收站目录，无需重新创建容器

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
│   │   │   ├── StatsBar.vue       # 顶部统计栏
│   │   │   ├── InfoPanel.vue      # 图片信息弹窗
│   │   │   ├── ConfirmDialog.vue  # 确认弹窗
│   │   │   └── SettingsPanel.vue  # 设置面板（含目录配置）
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
└── README.md
```

## 🚀 部署步骤（飞牛 NAS Docker）

### 1. 上传项目到 NAS

将整个 `photo-sorter` 文件夹上传到 NAS，例如放在 `/docker/photo-sorter/`

### 2. 创建数据目录

```bash
mkdir -p /docker/photo-sorter/db
```

### 3. 构建并启动

```bash
cd /docker/photo-sorter
docker-compose up -d --build
```

### 4. 访问应用

浏览器打开：`http://NAS-IP:8082`

### 5. 配置目录路径

首次打开后，点击左下角 ⚙️ 齿轮进入设置页面，配置：

- **图片源目录**：你 NAS 上存放照片的路径（如 `/nas/host/共享/photos`）
- **收藏目录**：收藏照片的存放路径（如 `/nas/host/共享/star_photos`）
- **回收站目录**：删除照片的存放路径（如 `/nas/host/共享/recycle_photos`）

> 💡 容器已将 NAS 根目录挂载到 `/nas/host`，所以 NAS 上的 `/共享/photos` 在容器内就是 `/nas/host/共享/photos`

## 🔧 配置说明

### 端口

默认 `8082`，修改 `docker-compose.yml` 中的 `ports` 映射即可。

### 挂载说明

`docker-compose.yml` 中将 NAS 根目录 `/` 挂载到容器 `/nas/host`（只读），容器通过此路径访问 NAS 上的任意文件夹。

### 黑名单时长

在设置页面修改，支持：1 年 / 3 年（默认）/ 永久

### 重复过滤

在设置页面开关。

## 📱 使用说明

| 手势 | 操作 |
|------|------|
| 右滑 | 保留照片，切换下一张 |
| 上滑 | 删除照片（移入回收站，二次确认） |
| 双击 | 收藏照片，触发动画 |
| 单击 | 查看图片信息 |

## 🛠️ 技术栈

- **前端**：Vue3 + Vite + TailwindCSS
- **后端**：Python3 + FastAPI + SQLite
- **容器**：Docker + python:3.10-slim
- **图片处理**：Pillow + pillow-heif（HEIC 支持）

## 📄 许可证

MIT License - 纯本地私有化运行，无任何外网依赖。
