# sakurafinder/core/scanner.py
from __future__ import annotations
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable, List, Optional
from ..models import FileRecord
from .utils import normalize_path, should_exclude, is_hidden


def _stat_to_record(path: str, st: os.stat_result, is_dir: bool) -> FileRecord:
    name = os.path.basename(path)
    ext = os.path.splitext(name)[1].lower().lstrip(".") if not is_dir else ""
    return FileRecord(
        path=path, name=name, ext=ext, size=st.st_size,
        ctime=st.st_ctime, mtime=st.st_mtime, atime=st.st_atime,
        is_dir=is_dir, is_hidden=is_hidden(path),
        is_readonly=not (st.st_mode & 0o200),
    )


class Scanner:
    """用 os.scandir 递归扫描；每个根目录一个任务，可多线程并行多个根。"""

    def __init__(self, excludes: Optional[List[str]] = None,
                 workers: int = 4):
        self.excludes = excludes or []
        self.workers = workers

    def scan_root(self, root: str,
                  on_batch: Callable[[List[FileRecord]], None],
                  batch_size: int = 1000) -> int:
        """扫描单个根目录，批量回调。返回记录数。"""
        root = normalize_path(root)
        if not os.path.isdir(root):
            return 0
        count = 0
        batch: List[FileRecord] = []
        stack = [root]
        while stack:
            cur = stack.pop()
            try:
                with os.scandir(cur) as it:
                    for entry in it:
                        full = entry.path
                        if should_exclude(full, self.excludes):
                            continue
                        try:
                            st = entry.stat(follow_symlinks=False)
                        except OSError:
                            continue
                        is_dir = entry.is_dir(follow_symlinks=False)
                        batch.append(_stat_to_record(full, st, is_dir))
                        if is_dir:
                            stack.append(full)
                        if len(batch) >= batch_size:
                            on_batch(batch)
                            count += len(batch)
                            batch = []
            except OSError:
                continue
        if batch:
            on_batch(batch)
            count += len(batch)
        return count

    def scan_roots(self, roots: Iterable[str],
                   on_batch: Callable[[List[FileRecord]], None]) -> int:
        total = 0
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futures = [pool.submit(self.scan_root, r, on_batch) for r in roots]
            for f in as_completed(futures):
                try:
                    total += f.result()
                except Exception:
                    pass
        return total