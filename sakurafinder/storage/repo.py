# sakurafinder/storage/repo.py
from __future__ import annotations
import sqlite3
from typing import Iterable, List, Tuple
from ..models import FileRecord
from .db import Database


class FileRepo:
    def __init__(self, db: Database):
        self.db = db

    # ---------- 写入 ----------
    def upsert_many(self, records: Iterable[FileRecord], batch_size: int = 500) -> int:
        rows: List[Tuple] = []
        count = 0
        sql = """
            INSERT INTO files(path,name,ext,size,ctime,mtime,atime,is_dir,is_hidden,is_readonly)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(path) DO UPDATE SET
                name=excluded.name, ext=excluded.ext, size=excluded.size,
                ctime=excluded.ctime, mtime=excluded.mtime, atime=excluded.atime,
                is_dir=excluded.is_dir, is_hidden=excluded.is_hidden,
                is_readonly=excluded.is_readonly
        """
        with self.db.cursor() as cur:
            for r in records:
                rows.append((r.path, r.name, r.ext, r.size,
                             r.ctime, r.mtime, r.atime,
                             int(r.is_dir), int(r.is_hidden), int(r.is_readonly)))
                if len(rows) >= batch_size:
                    cur.executemany(sql, rows)
                    count += len(rows)
                    rows.clear()
            if rows:
                cur.executemany(sql, rows)
                count += len(rows)
        return count

    def delete_by_paths(self, paths: Iterable[str]) -> int:
        with self.db.cursor() as cur:
            n = 0
            for p in paths:
                cur.execute("DELETE FROM files WHERE path = ?", (p,))
                n += cur.rowcount
            return n

    # ---------- 读取 ----------
    def get_by_path(self, path: str) -> FileRecord | None:
        with self.db.cursor() as cur:
            cur.execute("SELECT * FROM files WHERE path = ?", (path,))
            row = cur.fetchone()
            return self._row_to_record(row) if row else None

    def count(self) -> int:
        with self.db.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM files")
            return cur.fetchone()[0]

    def search_sql(self, where: str, params: list, order: str,
                   limit: int, offset: int) -> Tuple[List[FileRecord], int]:
        with self.db.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM files WHERE {where}", params)
            total = cur.fetchone()[0]
            cur.execute(
                f"SELECT * FROM files WHERE {where} ORDER BY {order} LIMIT ? OFFSET ?",
                [*params, limit, offset],
            )
            rows = cur.fetchall()
            return [self._row_to_record(r) for r in rows], total

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> FileRecord:
        return FileRecord(
            path=row["path"], name=row["name"], ext=row["ext"],
            size=row["size"], ctime=row["ctime"], mtime=row["mtime"],
            atime=row["atime"], is_dir=bool(row["is_dir"]),
            is_hidden=bool(row["is_hidden"]), is_readonly=bool(row["is_readonly"]),
        )