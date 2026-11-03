# sakurafinder/storage/db.py
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

SCHEMA_VERSION = 1

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS files (
    id         INTEGER PRIMARY KEY,
    path       TEXT NOT NULL UNIQUE,
    name       TEXT NOT NULL,
    ext        TEXT NOT NULL DEFAULT '',
    size       INTEGER NOT NULL,
    ctime      REAL NOT NULL,
    mtime      REAL NOT NULL,
    atime      REAL NOT NULL,
    is_dir     INTEGER NOT NULL DEFAULT 0,
    is_hidden  INTEGER NOT NULL DEFAULT 0,
    is_readonly INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_files_name   ON files(name);
CREATE INDEX IF NOT EXISTS idx_files_ext    ON files(ext);
CREATE INDEX IF NOT EXISTS idx_files_size   ON files(size);
CREATE INDEX IF NOT EXISTS idx_files_mtime  ON files(mtime);
CREATE INDEX IF NOT EXISTS idx_files_isdir  ON files(is_dir);

-- 可选全文索引（enable_content_index=True 时创建）
"""

FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
    path, name, content,
    content='files_content', content_rowid='id',
    tokenize='unicode61'
);
CREATE TABLE IF NOT EXISTS files_content (
    id INTEGER PRIMARY KEY,
    content TEXT
);
"""


class Database:
    def __init__(self, db_path: Path | str, enable_fts: bool = False):
        self.db_path = str(db_path)
        self.enable_fts = enable_fts
        self._init_schema()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30,
                               check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def cursor(self) -> Iterator[sqlite3.Cursor]:
        conn = self.connect()
        try:
            yield conn.cursor()
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self.cursor() as cur:
            cur.executescript(SCHEMA_SQL)
            if self.enable_fts:
                cur.executescript(FTS_SQL)
            cur.execute("INSERT OR IGNORE INTO meta(key,value) VALUES(?,?)",
                        ("schema_version", str(SCHEMA_VERSION)))