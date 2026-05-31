"""
图片服务 - EXIF解析、文件操作、随机算法、缓存、缩略图
"""
import hashlib
import os
import random
import shutil
import time
import threading
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from app.config import SUPPORTED_EXTENSIONS, VIDEO_EXTENSIONS, BLACKLIST_DURATION_OPTIONS, NAS_HOST_DIR, THUMBNAIL_DIR, THUMBNAIL_SIZE
from app.models.database import get_db

# 逆地理编码（GPS转省市区）
try:
    import reverse_geocoder as rg
    _RG_AVAILABLE = True
except ImportError:
    _RG_AVAILABLE = False
    print("[WARN] reverse_geocoder 未安装，GPS位置信息将显示坐标")

# 扫描锁，防止并发扫描
_scan_lock = threading.Lock()


def _gps_to_location(gps: dict) -> str | None:
    """将GPS坐标转换为省-市格式的位置信息"""
    if not gps or not _RG_AVAILABLE:
        return None
    try:
        result = rg.search((gps["lat"], gps["lng"]))
        if result:
            r = result[0]
            admin1 = r.get("admin1", "")
            name = r.get("name", "")
            cc = r.get("cc", "")
            if cc == "CN":
                parts = [p for p in [admin1, name] if p]
                return "-".join(parts) if parts else None
            else:
                parts = [p for p in [name, admin1] if p]
                return ", ".join(parts) if parts else None
    except Exception as e:
        print(f"逆地理编码失败: {e}")
    return None


def _to_container_path(user_path: str) -> str:
    """将用户填写的NAS路径自动转换为容器内路径"""
    if not user_path:
        return user_path
    user_path = user_path.strip()
    if user_path.startswith(str(NAS_HOST_DIR)):
        return user_path
    return str(NAS_HOST_DIR) + "/" + user_path.lstrip("/")


def _to_nas_path(container_path: str) -> str:
    """将容器内路径转回用户可读的NAS路径"""
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
    """计算文件MD5哈希（修复版，正确分块读取）"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
    except Exception as e:
        print(f"计算哈希失败: {file_path}, 错误: {e}")
        return ""
    return hash_md5.hexdigest()


def generate_thumbnail(img_path: Path, thumb_path: Path) -> bool:
    """生成缩略图，返回是否成功"""
    try:
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.open(img_path)
        # 根据 EXIF 方向自动旋转，把方向信息“烘焙”到像素中
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
        img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        # 统一转为 JPEG 节省空间
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(str(thumb_path), "JPEG", quality=80, optimize=True)
        return True
    except Exception as e:
        print(f"缩略图生成失败: {img_path}, 错误: {e}")
        return False


def _get_thumb_path(file_hash: str) -> Path:
    """根据文件哈希生成缩略图路径"""
    return THUMBNAIL_DIR / f"{file_hash}.jpg"


def generate_video_thumbnail(video_path: Path, thumb_path: Path) -> bool:
    """用ffmpeg提取视频第一帧作为缩略图"""
    try:
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        import subprocess
        result = subprocess.run(
            [
                "ffmpeg", "-i", str(video_path),
                "-ss", "00:00:01",  # 第1秒
                "-vframes", "1",
                "-vf", "scale=400:400:force_original_aspect_ratio=decrease",
                "-y", str(thumb_path)
            ],
            capture_output=True, timeout=30
        )
        return result.returncode == 0 and thumb_path.exists()
    except Exception as e:
        print(f"视频缩略图生成失败: {video_path}, 错误: {e}")
        return False


def get_video_metadata(video_path: Path) -> dict:
    """用ffprobe提取视频元数据"""
    try:
        import subprocess, json
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                str(video_path)
            ],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return {}
        data = json.loads(result.stdout)
        meta = {}
        # 从format获取时长
        fmt = data.get("format", {})
        if "duration" in fmt:
            meta["duration"] = float(fmt["duration"])
        # 从视频流获取分辨率
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                meta["width"] = stream.get("width")
                meta["height"] = stream.get("height")
                break
        return meta
    except Exception as e:
        print(f"视频元数据提取失败: {video_path}, 错误: {e}")
        return {}


def scan_photos(base_dir: Path) -> list[dict]:
    """扫描目录下所有支持的图片和视频文件"""
    photos = []
    if not base_dir.exists():
        return photos
    all_extensions = SUPPORTED_EXTENSIONS | VIDEO_EXTENSIONS
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            file_path = Path(root) / file
            ext = file_path.suffix.lower()
            if ext in all_extensions:
                try:
                    stat = file_path.stat()
                    media_type = "video" if ext in VIDEO_EXTENSIONS else "photo"
                    photos.append({
                        "path": str(file_path),
                        "name": file,
                        "dir": str(root),
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                        "media_type": media_type,
                    })
                except OSError:
                    continue
    return photos


def scan_and_cache(force: bool = False) -> dict:
    """扫描照片目录并缓存到数据库（增量更新）
    
    Args:
        force: 强制全量重新扫描（忽略缓存）
    
    Returns:
        扫描结果统计
    """
    if not _scan_lock.acquire(blocking=False):
        return {"status": "busy", "message": "扫描正在进行中"}

    try:
        dirs = _get_dirs()
        photos_dir = dirs.get("photos")
        if not photos_dir or not photos_dir.exists():
            return {"status": "error", "message": "照片目录未配置或不存在"}

        db = get_db()
        now = time.time()

        # 更新扫描状态
        db.execute(
            "UPDATE scan_status SET status='scanning', started_at=?, finished_at=NULL, new_count=0, updated_count=0, deleted_count=0, processed=0 WHERE id=1",
            (now,)
        )
        db.commit()

        # 读取数据库中已有的活跃照片（路径 → mtime 映射）
        cached = {}
        if force:
            # 强制模式：清空所有活跃照片记录，强制重新扫描+重新生成缩略图
            db.execute("UPDATE scan_status SET total=0 WHERE id=1")
            db.execute("DELETE FROM photos WHERE status='active'")
            db.commit()
        else:
            for row in db.execute("SELECT file_path, mtime FROM photos WHERE status='active'").fetchall():
                cached[row["file_path"]] = row["mtime"]

        # 扫描文件系统
        fs_photos = scan_photos(photos_dir)
        fs_paths = {p["path"] for p in fs_photos}
        total = len(fs_photos)

        db.execute("UPDATE scan_status SET total=? WHERE id=1", (total,))
        db.commit()

        new_count = 0
        updated_count = 0
        processed = 0

        THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

        for photo in fs_photos:
            fpath = photo["path"]
            fmtime = photo["mtime"]
            need_update = False

            if fpath not in cached:
                need_update = True
                new_count += 1
            elif cached[fpath] != fmtime:
                need_update = True
                updated_count += 1

            if need_update:
                p = Path(fpath)
                file_hash = compute_file_hash(p)
                media_type = photo.get("media_type", "photo")
                thumb_path = ""
                width = None
                height = None
                date = None
                gps_lat = None
                gps_lng = None
                location = None
                duration = None

                if media_type == "video":
                    # 视频：ffmpeg缩略图 + ffprobe元数据
                    vmeta = get_video_metadata(p)
                    width = vmeta.get("width")
                    height = vmeta.get("height")
                    duration = vmeta.get("duration")
                    if file_hash:
                        tp = _get_thumb_path(file_hash)
                        if not tp.exists():
                            generate_video_thumbnail(p, tp)
                        thumb_path = str(tp)
                else:
                    # 图片：EXIF + Pillow缩略图
                    exif = get_exif_data(p)
                    gps = exif.get("gps")
                    location = _gps_to_location(gps)
                    width = exif.get("width")
                    height = exif.get("height")
                    date = exif.get("date")
                    gps_lat = gps["lat"] if gps else None
                    gps_lng = gps["lng"] if gps else None
                    if file_hash:
                        tp = _get_thumb_path(file_hash)
                        if not tp.exists():
                            generate_thumbnail(p, tp)
                        thumb_path = str(tp)

                db.execute(
                    """INSERT OR REPLACE INTO photos 
                       (file_path, file_hash, file_size, mtime, width, height, date, gps_lat, gps_lng, location, thumb_path, dir, name, media_type, duration)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (fpath, file_hash, photo["size"], fmtime,
                     width, height, date, gps_lat, gps_lng,
                     location, thumb_path, photo["dir"], photo["name"],
                     media_type, duration)
                )

            processed += 1
            # 每处理50张提交一次并释放数据库锁
            if processed % 50 == 0:
                db.execute(
                    "UPDATE scan_status SET processed=?, new_count=?, updated_count=? WHERE id=1",
                    (processed, new_count, updated_count)
                )
                db.commit()
                db.close()  # 释放锁，让其他操作可以写入
                time.sleep(0.1)  # 给其他操作一点时间
                db = get_db()  # 重新打开连接

        # 活跃照片中不在文件系统的，标记为已删除
        deleted_count = 0
        if cached:
            missing = set(cached.keys()) - fs_paths
            if missing:
                for fpath in missing:
                    db.execute("UPDATE photos SET status='deleted', deleted_at=? WHERE file_path=? AND status='active'", (now, fpath))
                deleted_count = len(missing)

        # 最终提交
        db.execute(
            """UPDATE scan_status SET status='idle', total=?, processed=?, 
               new_count=?, updated_count=?, deleted_count=?, finished_at=? WHERE id=1""",
            (total, processed, new_count, updated_count, deleted_count, time.time())
        )
        db.commit()
        db.close()

        result = {
            "status": "done",
            "total": total,
            "new": new_count,
            "updated": updated_count,
            "deleted": deleted_count,
        }
        print(f"✅ 扫描完成: {result}")
        return result

    except Exception as e:
        print(f"❌ 扫描异常: {e}")
        try:
            db = get_db()
            db.execute("UPDATE scan_status SET status='error' WHERE id=1")
            db.commit()
            db.close()
        except:
            pass
        return {"status": "error", "message": str(e)}
    finally:
        _scan_lock.release()


def get_scan_status() -> dict:
    """获取扫描状态"""
    db = get_db()
    row = db.execute("SELECT * FROM scan_status WHERE id=1").fetchone()
    db.close()
    if row:
        return {
            "status": row["status"],
            "total": row["total"],
            "processed": row["processed"],
            "new_count": row["new_count"],
            "updated_count": row["updated_count"],
            "deleted_count": row["deleted_count"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
        }
    return {"status": "idle", "total": 0, "processed": 0}


def get_cached_photo_count() -> int:
    """获取缓存中的活跃照片数量"""
    db = get_db()
    row = db.execute("SELECT COUNT(*) as cnt FROM photos WHERE status='active'").fetchone()
    db.close()
    return row["cnt"] if row else 0


def get_random_photo(blacklist_duration_key: str = "3y", enable_duplicate_filter: bool = True, media_type: str = "photo") -> dict | None:
    """随机获取一张未浏览过的图片或视频（使用缓存）"""
    dirs = _get_dirs()
    photos_dir = dirs.get("photos")
    if not photos_dir or not photos_dir.exists():
        return None

    db = get_db()
    now = time.time()

    # 获取未过期的黑名单路径
    rows = db.execute(
        "SELECT file_path, file_hash FROM blacklist WHERE expires_at > ?",
        (now,)
    ).fetchall()
    blacklisted_paths = {r["file_path"] for r in rows}

    media_filter = "AND media_type = ?"

    if enable_duplicate_filter:
        blacklisted_hashes = {r["file_hash"] for r in rows if r["file_hash"]}
        if blacklisted_hashes:
            placeholders = ",".join("?" * len(blacklisted_hashes))
            candidates = db.execute(
                f"SELECT * FROM photos WHERE status='active' AND {media_filter} AND file_path NOT IN (SELECT file_path FROM blacklist WHERE expires_at > ?) AND (file_hash IS NULL OR file_hash NOT IN ({placeholders}))",
                [media_type, now] + list(blacklisted_hashes)
            ).fetchall()
        else:
            candidates = db.execute(
                f"SELECT * FROM photos WHERE status='active' AND {media_filter} AND file_path NOT IN (SELECT file_path FROM blacklist WHERE expires_at > ?)",
                (media_type, now)
            ).fetchall()
    else:
        candidates = db.execute(
            f"SELECT * FROM photos WHERE status='active' AND {media_filter} AND file_path NOT IN (SELECT file_path FROM blacklist WHERE expires_at > ?)",
            (media_type, now)
        ).fetchall()

    db.close()

    if not candidates:
        return None

    chosen = random.choice(candidates)
    gps = None
    if chosen["gps_lat"] is not None and chosen["gps_lng"] is not None:
        gps = {"lat": chosen["gps_lat"], "lng": chosen["gps_lng"]}

    return {
        "path": _to_nas_path(chosen["file_path"]),
        "name": chosen["name"],
        "dir": _to_nas_path(chosen["dir"]),
        "file_size": chosen["file_size"],
        "width": chosen["width"],
        "height": chosen["height"],
        "date": chosen["date"],
        "gps": gps,
        "location": chosen["location"],
        "thumb_path": chosen["thumb_path"],
        "file_hash": chosen["file_hash"],
        "media_type": chosen["media_type"] if "media_type" in chosen.keys() else "photo",
        "duration": chosen["duration"] if "duration" in chosen.keys() else None,
        "relative_path": str(Path(chosen["file_path"]).relative_to(photos_dir)) if str(chosen["file_path"]).startswith(str(photos_dir)) else chosen["name"],
    }


def add_to_blacklist(file_path: str, action: str = "viewed", duration_key: str = "3y"):
    """将图片加入黑名单（使用缓存的哈希）"""
    db = get_db()
    now = time.time()
    duration = BLACKLIST_DURATION_OPTIONS.get(duration_key, BLACKLIST_DURATION_OPTIONS["3y"])

    # 从缓存中获取哈希，避免重新计算
    settings_row = db.execute("SELECT value FROM settings WHERE key = 'enable_duplicate_filter'").fetchone()
    dup_filter = settings_row["value"] == "true" if settings_row else True

    file_hash = None
    if dup_filter:
        hash_row = db.execute("SELECT file_hash FROM photos WHERE file_path = ?", (file_path,)).fetchone()
        file_hash = hash_row["file_hash"] if hash_row else None

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
    """收藏图片 - 复制到收藏目录（去重，已收藏则跳过）"""
    dirs = _get_dirs()
    star_dir = dirs.get("star")
    if not star_dir:
        return {"success": False, "error": "收藏目录未配置，请在设置页面配置"}

    src = Path(file_path)
    if not src.exists():
        return {"success": False, "error": "文件不存在"}

    # 去重：检查是否已收藏过（通过 original_path 查询）
    db = get_db()
    existing = db.execute(
        "SELECT file_path FROM favorites WHERE original_path = ?",
        (file_path,)
    ).fetchone()
    if existing:
        db.close()
        return {"success": True, "dest": existing["file_path"], "message": "已收藏过"}

    star_dir.mkdir(parents=True, exist_ok=True)
    dest = star_dir / src.name

    counter = 1
    while dest.exists():
        dest = star_dir / f"{src.stem}_{counter}{src.suffix}"
        counter += 1

    try:
        shutil.copy2(str(src), str(dest))
        now = time.time()
        db.execute(
            "INSERT OR REPLACE INTO favorites (file_path, original_path, favorited_at) VALUES (?, ?, ?)",
            (str(dest), file_path, now)
        )
        db.execute(
            "UPDATE photos SET status='favorited' WHERE file_path=? AND status='active'",
            (file_path,)
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

    counter = 1
    while dest.exists():
        stem = src.stem
        suffix = src.suffix
        dest = recycle_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    try:
        file_size = src.stat().st_size
        shutil.move(str(src), str(dest))
        # 标记为已删除，更新路径到回收站
        db = get_db()
        now = time.time()
        db.execute(
            "UPDATE photos SET status='deleted', deleted_at=?, file_path=? WHERE file_path=? AND status='active'",
            (now, str(dest), file_path)
        )
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


def restore_photo(file_path: str) -> dict:
    """从回收站恢复照片到源目录"""
    dirs = _get_dirs()
    photos_dir = dirs.get("photos")
    if not photos_dir:
        return {"success": False, "error": "图片源目录未配置"}

    src = Path(file_path)
    if not src.exists():
        return {"success": False, "error": "文件不存在"}

    photos_dir.mkdir(parents=True, exist_ok=True)
    dest = photos_dir / src.name

    counter = 1
    while dest.exists():
        dest = photos_dir / f"{src.stem}_{counter}{src.suffix}"
        counter += 1

    try:
        shutil.move(str(src), str(dest))
        db = get_db()
        db.execute(
            "UPDATE photos SET status='active', deleted_at=NULL, file_path=? WHERE file_path=? AND status='deleted'",
            (str(dest), file_path)
        )
        db.commit()
        db.close()
        return {"success": True, "dest": str(dest), "message": f"已恢复到 {photos_dir.name}/"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def restore_all_photos() -> dict:
    """批量恢复回收站所有照片"""
    dirs = _get_dirs()
    photos_dir = dirs.get("photos")
    if not photos_dir:
        return {"success": False, "error": "图片源目录未配置"}

    db = get_db()
    rows = db.execute("SELECT file_path FROM photos WHERE status='deleted'").fetchall()
    photos_dir.mkdir(parents=True, exist_ok=True)
    restored = 0
    for row in rows:
        src = Path(row["file_path"])
        if not src.exists():
            continue
        dest = photos_dir / src.name
        counter = 1
        while dest.exists():
            dest = photos_dir / f"{src.stem}_{counter}{src.suffix}"
            counter += 1
        try:
            shutil.move(str(src), str(dest))
            db.execute(
                "UPDATE photos SET status='active', deleted_at=NULL, file_path=? WHERE file_path=?",
                (str(dest), str(src))
            )
            restored += 1
        except Exception:
            continue
    db.commit()
    db.close()
    return {"success": True, "restored": restored, "message": f"已恢复 {restored} 张照片"}


def get_deleted_photos() -> list:
    """获取回收站照片列表（从数据库查，含完整元数据）"""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM photos WHERE status='deleted' ORDER BY deleted_at DESC"
    ).fetchall()
    db.close()
    result = []
    for r in rows:
        thumb_url = None
        if r["file_hash"]:
            tp = _get_thumb_path(r["file_hash"])
            if tp.exists():
                thumb_url = f"/api/photo/thumbnail/{r['file_hash']}"
        result.append({
            "name": r["name"],
            "path": r["file_path"],
            "size": r["file_size"],
            "mtime": r["mtime"],
            "deleted_at": r["deleted_at"],
            "file_hash": r["file_hash"],
            "thumb_url": thumb_url,
            "date": r["date"],
            "location": r["location"],
        })
    return result


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
    for key in ("photos_dir", "star_dir", "recycle_dir"):
        if key in result and result[key]:
            result[key] = _to_nas_path(result[key])
    return result


def update_setting(key: str, value: str):
    """更新设置，目录路径自动转换"""
    db = get_db()
    if key in ("photos_dir", "star_dir", "recycle_dir"):
        value = _to_container_path(value)
    db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    db.commit()
    db.close()


def get_photo_count() -> int:
    """获取源目录图片总数（使用缓存）"""
    return get_cached_photo_count()


def get_directory_info(path_str: str) -> dict:
    """获取目录信息（用于设置页面验证路径）"""
    if not path_str:
        return {"exists": False, "photo_count": 0, "writable": False}
    container_path = _to_container_path(path_str)
    p = Path(container_path)
    exists = p.exists() and p.is_dir()
    writable = exists and os.access(p, os.W_OK)
    photo_count = len(scan_photos(p)) if exists else 0
    return {"exists": exists, "photo_count": photo_count, "writable": writable}
