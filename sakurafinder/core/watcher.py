# sakurafinder/core/watcher.py
from __future__ import annotations
import queue
import time
from dataclasses import dataclass
from typing import Iterable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from ..models import FileRecord
from .utils import normalize_path, should_exclude, is_hidden


@dataclass
class IndexEvent:
    action: str          # "upsert" | "delete"
    path: str
    record: Optional[FileRecord] = None


def _make_record(path: str) -> Optional[FileRecord]:
    import os
    try:
        st = os.stat(path, follow_symlinks=False)
    except OSError:
        return None
    is_dir = os.path.isdir(path)
    name = os.path.basename(path)
    ext = "" if is_dir else os.path.splitext(name)[1].lower().lstrip(".")
    return FileRecord(
        path=path, name=name, ext=ext, size=st.st_size,
        ctime=st.st_ctime, mtime=st.st_mtime, atime=st.st_atime,
        is_dir=is_dir, is_hidden=is_hidden(path),
        is_readonly=not (st.st_mode & 0o200),
    )


class _Handler(FileSystemEventHandler):
    def __init__(self, excludes, out_queue: "queue.Queue[IndexEvent]"):
        self.excludes = excludes
        self.q = out_queue

    def _maybe_push(self, action: str, path: str) -> None:
        path = normalize_path(path)
        if should_exclude(path, self.excludes):
            return
        if action == "upsert":
            rec = _make_record(path)
            if rec:
                self.q.put(IndexEvent("upsert", path, rec))
        else:
            self.q.put(IndexEvent("delete", path))

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory:
            self._maybe_push("upsert", event.src_path)

    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory:
            self._maybe_push("upsert", event.src_path)

    def on_deleted(self, event: FileSystemEvent):
        self._maybe_push("delete", event.src_path)

    def on_moved(self, event: FileSystemEvent):
        self._maybe_push("delete", event.src_path)
        self._maybe_push("upsert", event.dest_path)


class Watcher:
    def __init__(self, excludes: Optional[list] = None):
        self.excludes = excludes or []
        self.queue: "queue.Queue[IndexEvent]" = queue.Queue(maxsize=100_000)
        self._observer = Observer()
        self._started = False

    def start(self, roots: Iterable[str]) -> None:
        handler = _Handler(self.excludes, self.queue)
        for r in roots:
            try:
                self._observer.schedule(handler, normalize_path(r), recursive=True)
            except Exception:
                continue
        self._observer.start()
        self._started = True

    def stop(self) -> None:
        if self._started:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._started = False