"""
数据库模型 - SQLite（支持上下文管理器）
"""
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from app.config import DB_PATH, DB_DIR


def _create_connection():
    """创建数据库连接（内部使用）"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def get_db():
    """获取数据库连接（建议使用 with get_db() as db: 上下文管理器）

    兼容旧用法：db = get_db(); ...; db.close()
    """
    return _create_connection()


@contextmanager
def get_db_ctx():
    """数据库连接上下文管理器 — 自动 commit 和 close

    用法:
        with get_db_ctx() as db:
            db.execute("SELECT ...")
    """
    conn = _create_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """初始化数据库表"""
    conn = _create_connection()
    cursor = conn.cursor()

    # 黑名单表 - 已浏览的图片
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            file_hash TEXT,
            blacklisted_at REAL NOT NULL,
            expires_at REAL NOT NULL,
            action TEXT DEFAULT 'viewed'
        )
    """)

    # 收藏表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            original_path TEXT,
            favorited_at REAL NOT NULL
        )
    """)

    # 统计表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            viewed_count INTEGER DEFAULT 0,
            favorited_count INTEGER DEFAULT 0,
            deleted_count INTEGER DEFAULT 0,
            cleaned_bytes INTEGER DEFAULT 0,
            last_updated REAL
        )
    """)

    # 设置表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # 照片缓存表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            file_path TEXT PRIMARY KEY,
            file_hash TEXT,
            file_size INTEGER,
            mtime REAL,
            width INTEGER,
            height INTEGER,
            date TEXT,
            gps_lat REAL,
            gps_lng REAL,
            location TEXT,
            thumb_path TEXT,
            dir TEXT,
            name TEXT,
            status TEXT DEFAULT 'active',
            deleted_at REAL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_photos_hash ON photos(file_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_photos_dir ON photos(dir)")

    # 兼容旧数据库：添加缺失列
    cursor.execute("PRAGMA table_info(photos)")
    photo_columns = {row[1] for row in cursor.fetchall()}
    if 'status' not in photo_columns:
        cursor.execute("ALTER TABLE photos ADD COLUMN status TEXT DEFAULT 'active'")
    if 'deleted_at' not in photo_columns:
        cursor.execute("ALTER TABLE photos ADD COLUMN deleted_at REAL")
    if 'media_type' not in photo_columns:
        cursor.execute("ALTER TABLE photos ADD COLUMN media_type TEXT DEFAULT 'photo'")
    if 'duration' not in photo_columns:
        cursor.execute("ALTER TABLE photos ADD COLUMN duration REAL")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_photos_status ON photos(status)")

    # 扫描状态表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scan_status (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            status TEXT DEFAULT 'idle',
            total INTEGER DEFAULT 0,
            processed INTEGER DEFAULT 0,
            new_count INTEGER DEFAULT 0,
            updated_count INTEGER DEFAULT 0,
            deleted_count INTEGER DEFAULT 0,
            started_at REAL,
            finished_at REAL
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO scan_status (id, status) VALUES (1, 'idle')")

    # 兼容旧数据库：给 blacklist 表加 file_hash 列
    cursor.execute("PRAGMA table_info(blacklist)")
    columns = {row[1] for row in cursor.fetchall()}
    if 'file_hash' not in columns:
        cursor.execute("ALTER TABLE blacklist ADD COLUMN file_hash TEXT")

    # 初始化统计记录
    cursor.execute("SELECT COUNT(*) FROM stats")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO stats (viewed_count, favorited_count, deleted_count, cleaned_bytes, last_updated) VALUES (0, 0, 0, 0, ?)",
            (time.time(),)
        )

    # 初始化默认设置
    default_settings = {
        "blacklist_duration": "3y",
        "enable_duplicate_filter": "true",
        "photos_dir": "",
        "star_dir": "",
        "recycle_dir": "",
    }
    for key, value in default_settings.items():
        cursor.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )

    conn.commit()
    conn.close()
