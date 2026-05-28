import os
from pathlib import Path

# 基础路径配置
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = Path(os.getenv("DB_DIR", "/app/db"))
DB_PATH = DB_DIR / "photo_sorter.db"

# 容器内挂载的 NAS 根目录
NAS_HOST_DIR = Path(os.getenv("NAS_HOST_DIR", "/nas/host"))

# 默认目录（首次启动使用，之后以数据库设置为准）
DEFAULT_PHOTOS_DIR = os.getenv("PHOTOS_DIR", "")
DEFAULT_STAR_DIR = os.getenv("STAR_DIR", "")
DEFAULT_RECYCLE_DIR = os.getenv("RECYCLE_DIR", "")

# 服务配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8082"))

# 黑名单时长配置（秒）
BLACKLIST_DURATION_OPTIONS = {
    "1y": 365 * 24 * 3600,       # 1年
    "3y": 3 * 365 * 24 * 3600,   # 3年
    "forever": 999 * 365 * 24 * 3600,  # 永久
}
DEFAULT_BLACKLIST_DURATION = os.getenv("DEFAULT_BLACKLIST_DURATION", "3y")

# 支持的图片格式
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".bmp", ".gif", ".tiff"}

# 重复图片过滤
ENABLE_DUPLICATE_FILTER = os.getenv("ENABLE_DUPLICATE_FILTER", "true").lower() == "true"
