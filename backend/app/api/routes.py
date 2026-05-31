from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path

from app.services.photo_service import (
    get_random_photo, add_to_blacklist, favorite_photo, delete_photo,
    get_stats, get_blacklist_count, reset_blacklist, reset_stats,
    get_settings, update_setting, get_photo_count, get_directory_info,
    get_scan_status, scan_and_cache, get_cached_photo_count,
    _to_container_path, _get_thumb_path
)
from app.config import BLACKLIST_DURATION_OPTIONS, NAS_HOST_DIR

router = APIRouter(prefix="/api")


@router.get("/photo/random")
async def random_photo():
    """随机获取一张图片"""
    settings = get_settings()
    duration = settings.get("blacklist_duration", "3y")
    dup_filter = settings.get("enable_duplicate_filter", "true") == "true"

    photo = get_random_photo(blacklist_duration_key=duration, enable_duplicate_filter=dup_filter)
    if not photo:
        raise HTTPException(status_code=404, detail="没有更多可浏览的图片")

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
