"""
FastAPI 主入口
"""
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.routes import router
from app.models.database import init_db
from app.config import DEFAULT_PHOTOS_DIR, DEFAULT_STAR_DIR, DEFAULT_RECYCLE_DIR, DB_DIR, THUMBNAIL_DIR

app = FastAPI(title="去留 - 相册整理工具", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)


@app.on_event("startup")
async def startup():
    """启动时初始化"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    print("✅ 去留 相册整理工具已启动 (v2.0 - 缓存+缩略图)")
    print(f"📁 默认图片目录: {DEFAULT_PHOTOS_DIR or '(请在设置中配置)'}")
    print(f"⭐ 默认收藏目录: {DEFAULT_STAR_DIR or '(请在设置中配置)'}")
    print(f"🗑️ 默认回收站: {DEFAULT_RECYCLE_DIR or '(请在设置中配置)'}")
    print(f"💾 数据库: {DB_DIR}")
    print(f"🖼️ 缩略图: {THUMBNAIL_DIR}")

    # 后台启动首次扫描
    def _background_scan():
        from app.services.photo_service import scan_and_cache, get_cached_photo_count
        if get_cached_photo_count() == 0:
            print("📦 首次启动，开始后台扫描照片...")
            result = scan_and_cache(force=True)
            print(f"📦 首次扫描完成: {result}")
        else:
            # 增量扫描（检测新增/删除）
            result = scan_and_cache(force=False)
            if result.get("new", 0) > 0 or result.get("deleted", 0) > 0:
                print(f"📦 增量扫描完成: 新增 {result.get('new', 0)}, 删除 {result.get('deleted', 0)}")

    threading.Thread(target=_background_scan, daemon=True).start()


# 挂载前端静态文件
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
