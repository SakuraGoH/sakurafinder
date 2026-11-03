# sakurafinder/storage/__init__.py
"""存储层：SQLite 连接、记录读写、可选 FTS5 全文索引。"""
from __future__ import annotations

__all__ = ["Database", "FileRepo"]

from .db import Database
from .repo import FileRepo