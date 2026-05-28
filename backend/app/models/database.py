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
