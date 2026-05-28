"""
图片服务 - EXIF解析、文件操作、随机算法
"""
import hashlib
import os
import random
import shutil
import time
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from app.config import SUPPORTED_EXTENSIONS, BLACKLIST_DURATION_OPTIONS, NAS_HOST_DIR
from app.models.database import get_db


def _to_container_path(user_path: str) -> str:
    """将用户填写的NAS路径自动转换为容器内路径
    
    用户填 /vol1/xxx，自动转为 /nas/host/vol1/xxx
    如果已经以 /nas/host 开头则不重复转换
    """
    if not user_path:
        return user_path
    user_path = user_path.strip()
    if user_path.startswith(str(NAS_HOST_DIR)):
        return user_path
    # 去掉开头的斜杠再拼接
    return str(NAS_HOST_DIR) + "/" + user_path.lstrip("/")


def _to_nas_path(container_path: str) -> str:
    """将容器内路径转回用户可读的NAS路径
    
    /nas/host/vol1/xxx → /vol1/xxx
    """
    prefix = str(NAS_HOST_DIR) + "/"
    if container_path.startswith(prefix):
        return "/" + container_path[len(prefix):]
    return container_path


def _get_dirs() -> dict:
    """从数据库读取当前目录配置，自动转换路径"""
    db = get_db()
    rows = db.execute("SELECT key, value FROM settings WHERE key IN ('photos_dir', 'star_dir', 'recycle_dir')").fetchall()
    db.close()
    dirs = {r["key"]: r["value"] for r in rows}
    return {
        "photos": Path(_to_container_path(dirs.get("photos_dir", ""))) if dirs.get("photos_dir") else None,
        "star": Path(_to_container_path(dirs.get("star_dir", ""))) if dirs.get("star_dir") else None,
        "recycle": Path(_to_container_path(dirs.get("recycle_dir", ""))) if dirs.get("recycle_dir") else None,
    }


def get_exif_data(img_path: Path) -> dict:
    """解析图片EXIF信息"""
    exif_info = {
        "date": None,
        "gps": None,
        "width": None,
        "height": None,
        "file_size": None,
    }
    try:
        exif_info["file_size"] = img_path.stat().st_size
        img = Image.open(img_path)
        exif_info["width"] = img.width
        exif_info["height"] = img.height

        exif_data = img._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "DateTimeOriginal":
                    try:
                        exif_info["date"] = value
                    except:
                        pass
                elif tag == "GPSInfo":
                    gps_data = {}
                    for gps_tag_id in value:
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_data[gps_tag] = value[gps_tag_id]
                    if "GPSLatitude" in gps_data and "GPSLongitude" in gps_data:
                        lat = _convert_to_degrees(gps_data["GPSLatitude"])
                        lng = _convert_to_degrees(gps_data["GPSLongitude"])
                        if gps_data.get("GPSLatitudeRef") == "S":
                            lat = -lat
                        if gps_data.get("GPSLongitudeRef") == "W":
                            lng = -lng
                        exif_info["gps"] = {"lat": round(lat, 6), "lng": round(lng, 6)}
    except Exception as e:
        print(f"EXIF解析失败: {img_path}, 错误: {e}")
    return exif_info


def _convert_to_degrees(value):
    """将GPS坐标转换为度数"""
    d, m, s = value
    return d + (m / 60.0) + (s / 3600.0)


def compute_file_hash(file_path: Path) -> str:
    """计算文件哈希（用于去重）"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: 8192, b""):
                hash_md5.update(chunk)
    except:
        return ""
    return hash_md5.hexdigest()


def scan_photos(base_dir: Path) -> list[dict]:
    """扫描目录下所有支持的图片文件"""
    photos = []
    if not base_dir.exists():
        return photos

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                photos.append({
                    "path": str(file_path),
                    "name": file,
                    "dir": str(root),
                    "size": file_path.stat().st_size,
                })
    return photos


def get_random_photo(blacklist_duration_key: str = "3y", enable_duplicate_filter: bool = True) -> dict | None:
    """随机获取一张未浏览过的图片"""
    dirs = _get_dirs()
    photos_dir = dirs.get("photos")
    if not photos_dir or not photos_dir.exists():
        return None

    db = get_db()
    now = time.time()

    # 获取未过期的黑名单
    rows = db.execute(
        "SELECT file_path, file_hash FROM blacklist WHERE expires_at > ?",
        (now,)
    ).fetchall()
    blacklisted_paths = {r["file_path"] for r in rows}
    blacklisted_hashes = {r["file_hash"] for r in rows if r["file_hash"]}
    db.close()

    # 扫描所有图片
    all_photos = scan_photos(photos_dir)
    if not all_photos:
        return None

    # 过滤黑名单
    candidates = [p for p in all_photos if p["path"] not in blacklisted_paths]

    # 可选：重复图片过滤
    if enable_duplicate_filter:
        candidates = [p for p in candidates if compute_file_hash(Path(p["path"])) not in blacklisted_hashes]

    if not candidates:
        return None

    # 随机选择
    chosen = random.choice(candidates)
    photo_path = Path(chosen["path"])

    # 解析EXIF
    exif = get_exif_data(photo_path)

    return {
        "path": _to_nas_path(chosen["path"]),
        "name": chosen["name"],
        "dir": _to_nas_path(chosen["dir"]),
        "file_size": exif.get("file_size") or photo_path.stat().st_size,
        "width": exif.get("width"),
        "height": exif.get("height"),
        "date": exif.get("date"),
        "gps": exif.get("gps"),
        "relative_path": str(photo_path.relative_to(photos_dir)) if str(photo_path).startswith(str(photos_dir)) else chosen["name"],
    }


def add_to_blacklist(file_path: str, action: str = "viewed", duration_key: str = "3y"):
    """将图片加入黑名单"""
    db = get_db()
    now = time.time()
    duration = BLACKLIST_DURATION_OPTIONS.get(duration_key, BLACKLIST_DURATION_OPTIONS["3y"])

    # 读取去重设置
    settings_row = db.execute("SELECT value FROM settings WHERE key = 'enable_duplicate_filter'").fetchone()
    dup_filter = settings_row["value"] == "true" if settings_row else True

    file_hash = compute_file_hash(Path(file_path)) if dup_filter else None

    db.execute(
        """INSERT OR REPLACE INTO blacklist (file_path, file_hash, blacklisted_at, expires_at, action)
           VALUES (?, ?, ?, ?, ?)""",
        (file_path, file_hash, now, now + duration, action)
    )
    db.execute(
        "UPDATE stats SET viewed_count = viewed_count + 1, last_updated = ? WHERE id = 1",
        (now,)
    )
    db.commit()
    db.close()


def favorite_photo(file_path: str) -> dict:
    """收藏图片 - 复制到收藏目录"""
    dirs = _get_dirs()
    star_dir = dirs.get("star")
    if not star_dir:
        return {"success": False, "error": "收藏目录未配置，请在设置页面配置"}

    src = Path(file_path)
    if not src.exists():
        return {"success": False, "error": "文件不存在"}

    star_dir.mkdir(parents=True, exist_ok=True)
    dest = star_dir / src.name

    # 避免重名
    counter = 1
    while dest.exists():
        stem = src.stem
        suffix = src.suffix
        dest = star_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    try:
        shutil.copy2(str(src), str(dest))
        db = get_db()
        now = time.time()
        db.execute(
            "INSERT OR REPLACE INTO favorites (file_path, original_path, favorited_at) VALUES (?, ?, ?)",
            (str(dest), file_path, now)
        )
        db.execute(
            "UPDATE stats SET favorited_count = favorited_count + 1, last_updated = ? WHERE id = 1",
            (now,)
        )
        db.commit()
        db.close()
        return {"success": True, "dest": str(dest)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_photo(file_path: str) -> dict:
    """删除图片 - 移动到回收站目录"""
    dirs = _get_dirs()
    recycle_dir = dirs.get("recycle")
    if not recycle_dir:
        return {"success": False, "error": "回收站目录未配置，请在设置页面配置"}

    src = Path(file_path)
    if not src.exists():
        return {"success": False, "error": "文件不存在"}

    recycle_dir.mkdir(parents=True, exist_ok=True)
    dest = recycle_dir / src.name

    # 避免重名
    counter = 1
    while dest.exists():
        stem = src.stem
        suffix = src.suffix
        dest = recycle_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    try:
        file_size = src.stat().st_size
        shutil.move(str(src), str(dest))
        db = get_db()
        now = time.time()
        db.execute(
            "UPDATE stats SET deleted_count = deleted_count + 1, cleaned_bytes = cleaned_bytes + ?, last_updated = ? WHERE id = 1",
            (file_size, now)
        )
        db.commit()
        db.close()
        return {"success": True, "dest": str(dest), "cleaned_bytes": file_size}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_stats() -> dict:
    """获取统计数据"""
    db = get_db()
    row = db.execute("SELECT * FROM stats WHERE id = 1").fetchone()
    db.close()
    if row:
        return {
            "viewed_count": row["viewed_count"],
            "favorited_count": row["favorited_count"],
            "deleted_count": row["deleted_count"],
            "cleaned_bytes": row["cleaned_bytes"],
            "cleaned_mb": round(row["cleaned_bytes"] / (1024 * 1024), 2),
        }
    return {"viewed_count": 0, "favorited_count": 0, "deleted_count": 0, "cleaned_bytes": 0, "cleaned_mb": 0}


def get_blacklist_count() -> int:
    """获取黑名单数量"""
    db = get_db()
    row = db.execute("SELECT COUNT(*) as cnt FROM blacklist WHERE expires_at > ?", (time.time(),)).fetchone()
    db.close()
    return row["cnt"] if row else 0


def reset_blacklist():
    """重置黑名单"""
    db = get_db()
    db.execute("DELETE FROM blacklist")
    db.commit()
    db.close()


def reset_stats():
    """重置统计数据"""
    db = get_db()
    db.execute(
        "UPDATE stats SET viewed_count=0, favorited_count=0, deleted_count=0, cleaned_bytes=0, last_updated=? WHERE id=1",
        (time.time(),)
    )
    db.commit()
    db.close()


def get_settings() -> dict:
    """获取所有设置，路径转为用户可读格式"""
    db = get_db()
    rows = db.execute("SELECT key, value FROM settings").fetchall()
    db.close()
    result = {r["key"]: r["value"] for r in rows}
    # 目录类设置转回NAS路径显示
    for key in ("photos_dir", "star_dir", "recycle_dir"):
        if key in result and result[key]:
            result[key] = _to_nas_path(result[key])
    return result


def update_setting(key: str, value: str):
    """更新设置，目录路径自动转换"""
    db = get_db()
    # 目录类设置自动加 /nas/host 前缀
    if key in ("photos_dir", "star_dir", "recycle_dir"):
        value = _to_container_path(value)
    db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    db.commit()
    db.close()


def get_photo_count() -> int:
    """获取源目录图片总数"""
    dirs = _get_dirs()
    photos_dir = dirs.get("photos")
    if not photos_dir or not photos_dir.exists():
        return 0
    return len(scan_photos(photos_dir))


def get_directory_info(path_str: str) -> dict:
    """获取目录信息（用于设置页面验证路径）"""
    if not path_str:
        return {"exists": False, "photo_count": 0, "writable": False}
    # 自动转换用户填写的路径
    container_path = _to_container_path(path_str)
    p = Path(container_path)
    exists = p.exists() and p.is_dir()
    writable = exists and os.access(p, os.W_OK)
    photo_count = len(scan_photos(p)) if exists else 0
    return {"exists": exists, "photo_count": photo_count, "writable": writable}
