"""
数据库模型 - SQLite
"""
import sqlite3
import time
from pathlib import Path
from app.config import DB_PATH, DB_DIR


def get_db():
    """获取数据库连接"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")  # 等待锁释放，避免 database locked
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db()
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

    # 照片缓存表（新增）
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
            name TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_photos_hash ON photos(file_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_photos_dir ON photos(dir)")

    # 扫描状态表（新增）
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

    # 兼容旧数据库：给 blacklist 表加 file_hash 列（如果缺失）
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

    # 初始化默认设置（目录路径为空，用户首次启动后在设置页面配置）
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
