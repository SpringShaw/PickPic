"""
FastAPI 主入口
"""
import logging
import threading
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path

from app.api.routes import router
from app.models.database import init_db
from app.config import DEFAULT_PHOTOS_DIR, DEFAULT_STAR_DIR, DEFAULT_RECYCLE_DIR, DB_DIR, THUMBNAIL_DIR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("photo-sorter")

app = FastAPI(title="去留 - 相册整理工具", version="2.0.0")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("未处理的异常: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"}
    )

# CORS（本地 NAS 工具，允许同源及局域网访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
    logger.info("去留 相册整理工具已启动 (v2.0 - 缓存+缩略图)")
    logger.info("默认图片目录: %s", Path(DEFAULT_PHOTOS_DIR).name if DEFAULT_PHOTOS_DIR else '(请在设置中配置)')
    logger.info("默认收藏目录: %s", Path(DEFAULT_STAR_DIR).name if DEFAULT_STAR_DIR else '(请在设置中配置)')
    logger.info("默认回收站: %s", Path(DEFAULT_RECYCLE_DIR).name if DEFAULT_RECYCLE_DIR else '(请在设置中配置)')
    logger.debug("数据库: %s", DB_DIR)
    logger.debug("缩略图: %s", THUMBNAIL_DIR)

    # 后台启动首次扫描
    def _background_scan():
        from app.services.photo_service import scan_and_cache, get_cached_photo_count
        if get_cached_photo_count() == 0:
            logger.info("首次启动，开始后台扫描照片...")
            result = scan_and_cache(force=True)
            logger.info("首次扫描完成: %s", result)
        else:
            result = scan_and_cache(force=False)
            if result.get("new", 0) > 0 or result.get("deleted", 0) > 0:
                logger.info("增量扫描完成: 新增 %s, 删除 %s", result.get('new', 0), result.get('deleted', 0))

    threading.Thread(target=_background_scan, daemon=True).start()


# 挂载前端静态文件
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
