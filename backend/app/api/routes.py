from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
import re
import logging
import time
from pathlib import Path

from app.services.photo_service import (
    get_random_photo, add_to_blacklist, favorite_photo, delete_photo,
    get_favorites, unfavorite_photo, delete_favorite_photo,
    get_stats, get_blacklist_count, reset_blacklist, reset_stats,
    get_settings, update_setting, get_photo_count, get_directory_info,
    get_scan_status, scan_and_cache, get_cached_photo_count,
    _to_container_path, _get_thumb_path, _validate_path_in_dir,
    get_deleted_photos, restore_photo, restore_all_photos,
    empty_recycle
)
from app.config import BLACKLIST_DURATION_OPTIONS, NAS_HOST_DIR, THUMBNAIL_DIR

logger = logging.getLogger("pickpic")

router = APIRouter(prefix="/api")


@router.get("/photo/random")
async def random_photo(media_type: str = "photo"):
    """随机获取一张图片或视频"""
    if media_type not in ("photo", "video"):
        raise HTTPException(status_code=400, detail="media_type must be 'photo' or 'video'")
    settings = get_settings()
    duration = settings.get("blacklist_duration", "3y")
    dup_filter = settings.get("enable_duplicate_filter", "true") == "true"

    photo = get_random_photo(blacklist_duration_key=duration, enable_duplicate_filter=dup_filter, media_type=media_type)
    if not photo:
        raise HTTPException(status_code=404, detail="没有更多可浏览的{}".format("视频" if media_type == "video" else "图片"))

    # 加入黑名单（path是NAS路径，需转容器路径存储）
    add_to_blacklist(_to_container_path(photo["path"]), action="viewed", duration_key=duration)

    return {
        "success": True,
        "data": photo,
        "remaining": get_photo_count() - get_blacklist_count(),
    }


@router.get("/photo/image")
async def serve_image(path: str = Query(..., max_length=4096)):
    """提供图片文件"""
    container_path = _to_container_path(path)
    img_path = Path(container_path)
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="图片不存在")

    # 安全校验：文件必须在已配置的目录内
    resolved = img_path.resolve()
    allowed = False

    # 1) 优先校验 photos_dir（Docker 直挂 / 本地开发）
    settings = get_settings()
    photos_dir = settings.get("photos_dir", "")
    if photos_dir:
        try:
            resolved.relative_to(Path(_to_container_path(photos_dir)).resolve())
            allowed = True
        except ValueError:
            pass

    # 2) 回退校验 NAS_HOST_DIR（旧 NAS 部署兼容）
    if not allowed:
        try:
            resolved.relative_to(NAS_HOST_DIR.resolve())
            allowed = True
        except ValueError:
            pass

    if not allowed:
        raise HTTPException(status_code=403, detail="无权访问该路径")

    suffix = img_path.suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
        ".heic": "image/heic", ".heif": "image/heif",
        ".bmp": "image/bmp", ".gif": "image/gif",
        ".tiff": "image/tiff",
        ".mp4": "video/mp4", ".mov": "video/quicktime",
        ".avi": "video/x-msvideo", ".mkv": "video/x-matroska",
        ".webm": "video/webm", ".3gp": "video/3gpp",
        ".flv": "video/x-flv",
    }
    media_type = mime_map.get(suffix, "application/octet-stream")
    return FileResponse(str(img_path), media_type=media_type)


@router.get("/photo/thumbnail/{file_hash}")
async def serve_thumbnail(file_hash: str):
    """提供缩略图文件"""
    if not re.fullmatch(r'[a-fA-F0-9]+', file_hash):
        raise HTTPException(status_code=400, detail="无效的哈希值")
    thumb_path = _get_thumb_path(file_hash)
    try:
        thumb_path.resolve().relative_to(THUMBNAIL_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="无权访问")
    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="缩略图不存在")
    return FileResponse(str(thumb_path), media_type="image/jpeg")


@router.get("/favorites")
async def list_favorites():
    """获取收藏夹列表"""
    photos = get_favorites()
    return {"success": True, "data": photos}


@router.post("/favorites/unfavorite")
async def unfavorite(file_path: str = Query(..., max_length=4096)):
    """取消收藏"""
    try:
        _validate_path_in_dir(_to_container_path(file_path), "star")
    except ValueError as e:
        logger.warning("路径验证失败: %s", e)
        raise HTTPException(status_code=403, detail="无权访问该路径")
    result = unfavorite_photo(_to_container_path(file_path))
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.delete("/favorites/delete")
async def delete_fav(file_path: str = Query(..., max_length=4096)):
    """从收藏夹删除（移入回收站）"""
    try:
        _validate_path_in_dir(_to_container_path(file_path), "star")
    except ValueError as e:
        logger.warning("路径验证失败: %s", e)
        raise HTTPException(status_code=403, detail="无权访问该路径")
    result = delete_favorite_photo(_to_container_path(file_path))
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/photo/favorite")
async def favorite(file_path: str = Query(..., max_length=4096)):
    """收藏图片"""
    try:
        _validate_path_in_dir(_to_container_path(file_path), "photos")
    except ValueError as e:
        logger.warning("路径验证失败: %s", e)
        raise HTTPException(status_code=403, detail="无权访问该路径")
    result = favorite_photo(_to_container_path(file_path))
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/photo/delete")
async def delete(file_path: str = Query(..., max_length=4096)):
    """删除图片（移入回收站）"""
    try:
        _validate_path_in_dir(_to_container_path(file_path), "photos")
    except ValueError as e:
        logger.warning("路径验证失败: %s", e)
        raise HTTPException(status_code=403, detail="无权访问该路径")
    result = delete_photo(_to_container_path(file_path))
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/stats")
async def stats():
    """获取统计数据"""
    data = get_stats()
    data["blacklist_count"] = get_blacklist_count()
    data["total_photos"] = get_photo_count()
    data["cached_photos"] = get_cached_photo_count()
    return {"success": True, "data": data}


@router.post("/blacklist/reset")
async def api_reset_blacklist():
    """重置黑名单"""
    reset_blacklist()
    return {"success": True, "message": "黑名单已重置"}


@router.post("/stats/reset")
async def api_reset_stats():
    """重置统计"""
    reset_stats()
    return {"success": True, "message": "统计数据已重置"}


@router.get("/settings")
async def api_get_settings():
    """获取设置"""
    data = get_settings()
    data["blacklist_duration_options"] = list(BLACKLIST_DURATION_OPTIONS.keys())
    data["nas_host_dir"] = str(NAS_HOST_DIR)
    return {"success": True, "data": data}


@router.post("/settings")
async def api_update_settings(key: str = Query(..., max_length=128), value: str = Query(..., max_length=4096)):
    """更新设置"""
    allowed_keys = {"blacklist_duration", "enable_duplicate_filter", "photos_dir", "star_dir", "recycle_dir"}
    if key not in allowed_keys:
        raise HTTPException(status_code=400, detail=f"不允许修改设置: {key}")
    if key == "blacklist_duration" and value not in BLACKLIST_DURATION_OPTIONS:
        raise HTTPException(status_code=400, detail=f"无效的黑名单时长: {value}")
    if key == "enable_duplicate_filter" and value not in ("true", "false"):
        raise HTTPException(status_code=400, detail="enable_duplicate_filter 必须为 true 或 false")
    update_setting(key, value)
    return {"success": True, "message": f"设置 {key} 已更新为 {value}"}


@router.get("/dir/check")
async def check_directory(path: str = Query(..., max_length=4096)):
    """验证目录路径是否可用"""
    info = get_directory_info(path)
    return {"success": True, "data": info}


@router.post("/scan")
async def api_scan(background_tasks: BackgroundTasks, force: bool = False):
    """触发照片扫描（后台执行）"""
    background_tasks.add_task(scan_and_cache, force=force)
    return {"success": True, "message": "扫描已启动，请查看状态"}


@router.get("/scan/status")
async def api_scan_status():
    """获取扫描状态"""
    status = get_scan_status()
    return {"success": True, "data": status}


@router.get("/recycle")
async def api_recycle_list():
    """获取回收站照片列表（从数据库查，含缩略图和元数据）"""
    photos = get_deleted_photos()
    return {"success": True, "data": photos, "count": len(photos)}


@router.post("/recycle/restore")
async def api_recycle_restore(file_path: str = Query(..., max_length=4096)):
    """从回收站恢复照片到源目录"""
    container_path = _to_container_path(file_path)
    try:
        _validate_path_in_dir(container_path, "recycle")
    except ValueError as e:
        logger.warning("路径验证失败: %s", e)
        raise HTTPException(status_code=403, detail="无权访问该路径")
    result = restore_photo(container_path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/recycle/restore-all")
async def api_recycle_restore_all():
    """批量恢复回收站所有照片"""
    result = restore_all_photos()
    return result


@router.delete("/recycle/delete")
async def api_recycle_delete(file_path: str = Query(..., max_length=4096)):
    """永久删除回收站中的单条记录"""
    container_path = _to_container_path(file_path)
    try:
        _validate_path_in_dir(container_path, "recycle")
    except ValueError as e:
        logger.warning("路径验证失败: %s", e)
        raise HTTPException(status_code=403, detail="无权访问该路径")
    p = Path(container_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    try:
        file_size = p.stat().st_size
        p.unlink()
        from app.models.database import get_db
        db = get_db()
        db.execute("DELETE FROM photos WHERE file_path=? AND status='deleted'", (container_path,))
        db.execute(
            "UPDATE stats SET deleted_count=MAX(0, deleted_count-1), cleaned_bytes=MAX(0, cleaned_bytes-?), last_updated=? WHERE id=1",
            (file_size, time.time())
        )
        db.commit()
        db.close()
        return {"success": True, "message": "已永久删除"}
    except Exception as e:
        logger.exception("永久删除文件失败: %s", e)
        raise HTTPException(status_code=500, detail="删除失败，请稍后重试")


@router.delete("/recycle/empty")
async def api_recycle_empty():
    """清空回收站（永久删除全部）"""
    result = empty_recycle()
    return result
