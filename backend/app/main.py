"""
FastAPI 主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.routes import router
from app.models.database import init_db
from app.config import DEFAULT_PHOTOS_DIR, DEFAULT_STAR_DIR, DEFAULT_RECYCLE_DIR, DB_DIR

app = FastAPI(title="去留 - 相册整理工具", version="1.0.0")

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
    # 确保 DB_DIR 存在
    DB_DIR.mkdir(parents=True, exist_ok=True)
    # 初始化数据库
    init_db()
    print("✅ 去留 相册整理工具已启动")
    print(f"📁 默认图片目录: {DEFAULT_PHOTOS_DIR or '(请在设置中配置)'}")
    print(f"⭐ 默认收藏目录: {DEFAULT_STAR_DIR or '(请在设置中配置)'}")
    print(f"🗑️ 默认回收站: {DEFAULT_RECYCLE_DIR or '(请在设置中配置)'}")
    print(f"💾 数据库: {DB_DIR}")


# 挂载前端静态文件
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
