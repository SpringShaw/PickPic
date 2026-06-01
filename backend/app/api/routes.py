from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path

from app.services.photo_service import (
    get_random_photo, add_to_blacklist, favorite_photo, delete_photo,
    get_favorites, unfavorite_photo, delete_favorite_photo,
    get_stats, get_blacklist_count, reset_blacklist, reset_stats,
    get_settings, update_setting, get_photo_count, get_directory_info,
    get_scan_status, scan_and_cache, get_cached_photo_count,
    _to_container_path, _get_thumb_path,
    get_deleted_photos, restore_photo, restore_all_photos
)
from app.config import BLACKLIST_DURATION_OPTIONS, NAS_HOST_DIR

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
async def serve_image(path: str):
    """提供图片文件"""
    container_path = _to_container_path(path)
    img_path = Path(container_path)
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="图片不存在")

    try:
        img_path.resolve().relative_to(NAS_HOST_DIR.resolve())
    except ValueError:
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
    thumb_path = _get_thumb_path(file_hash)
    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="缩略图不存在")
    return FileResponse(str(thumb_path), media_type="image/jpeg")


@router.get("/favorites")
async def list_favorites():
    """获取收藏夹列表"""
    photos = get_favorites()
    return {"success": True, "data": photos}


@router.post("/favorites/unfavorite")
async def unfavorite(file_path: str):
    """取消收藏"""
    result = unfavorite_photo(_to_container_path(file_path))
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.delete("/favorites/delete")
async def delete_fav(file_path: str):
    """从收藏夹删除（移入回收站）"""
    result = delete_favorite_photo(_to_container_path(file_path))
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/photo/favorite")
async def favorite(file_path: str):
    """收藏图片"""
    result = favorite_photo(_to_container_path(file_path))
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/photo/delete")
async def delete(file_path: str):
    """删除图片（移入回收站）"""
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
async def api_update_settings(key: str, value: str):
    """更新设置"""
    allowed_keys = {"blacklist_duration", "enable_duplicate_filter", "photos_dir", "star_dir", "recycle_dir"}
    if key not in allowed_keys:
        raise HTTPException(status_code=400, detail=f"不允许修改设置: {key}")
    update_setting(key, value)
    return {"success": True, "message": f"设置 {key} 已更新为 {value}"}


@router.get("/dir/check")
async def check_directory(path: str):
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
async def api_recycle_restore(file_path: str):
    """从回收站恢复照片到源目录"""
    result = restore_photo(file_path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/recycle/restore-all")
async def api_recycle_restore_all():
    """批量恢复回收站所有照片"""
    result = restore_all_photos()
    return result


@router.delete("/recycle/delete")
async def api_recycle_delete(file_path: str):
    """永久删除回收站中的单条记录"""
    container_path = _to_container_path(file_path)
    p = Path(container_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    try:
        p.unlink()
        # 从数据库中删除记录
        from app.models.database import get_db
        db = get_db()
        db.execute("DELETE FROM photos WHERE file_path=? AND status='deleted'", (container_path,))
        db.commit()
        db.close()
        return {"success": True, "message": "已永久删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/recycle/empty")
async def api_recycle_empty():
    """清空回收站（永久删除全部）"""
    dirs = _get_dirs()
    recycle_dir = dirs.get("recycle")
    if not recycle_dir or not recycle_dir.exists():
        return {"success": True, "deleted": 0, "message": "回收站为空"}

    photos = scan_photos(recycle_dir)
    deleted = 0
    for p in photos:
        try:
            Path(p["path"]).unlink()
            deleted += 1
        except Exception:
            continue
    # 清空数据库中的deleted记录
    from app.models.database import get_db
    db = get_db()
    db.execute("DELETE FROM photos WHERE status='deleted'")
    db.commit()
    db.close()
    return {"success": True, "deleted": deleted, "message": f"已永久删除 {deleted} 个文件"}
