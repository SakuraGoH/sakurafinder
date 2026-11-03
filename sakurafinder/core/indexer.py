# sakurafinder/core/indexer.py
from __future__ import annotations
import queue
import threading
import time
from typing import List, Optional
from ..storage.repo import FileRepo
from .watcher import Watcher, IndexEvent


class IndexWriter:
    """从 Watcher 队列里批量消费事件，落库；可同时用于初始扫描结果。"""

    def __init__(self, repo: FileRepo, watcher: Optional[Watcher] = None,
                 flush_interval: float = 0.5, batch_size: int = 1000):
        self.repo = repo
        self.watcher = watcher
        self.flush_interval = flush_interval
        self.batch_size = batch_size
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)

    def _run(self) -> None:
        if not self.watcher:
            return
        upserts: List = []
        deletes: List[str] = []
        last_flush = time.time()
        while not self._stop.is_set():
            try:
                ev: IndexEvent = self.watcher.queue.get(timeout=0.2)
                if ev.action == "upsert" and ev.record:
                    upserts.append(ev.record)
                elif ev.action == "delete":
                    deletes.append(ev.path)
            except queue.Empty:
                pass
            now = time.time()
            if (len(upserts) + len(deletes) >= self.batch_size
                    or (now - last_flush >= self.flush_interval
                        and (upserts or deletes))):
                self._flush(upserts, deletes)
                upserts, deletes = [], []
                last_flush = now

    def _flush(self, upserts, deletes) -> None:
        try:
            if deletes:
                self.repo.delete_by_paths(deletes)
            if upserts:
                self.repo.upsert_many(upserts)
        except Exception as e:
            # 建议换成 logging
            print(f"[indexer] flush error: {e}")