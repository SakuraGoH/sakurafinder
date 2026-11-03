# sakurafinder/daemon.py
from __future__ import annotations
import argparse
import signal
import sys
import threading
import time
from .config import load_config
from .storage.db import Database
from .storage.repo import FileRepo
from .core.scanner import Scanner
from .core.watcher import Watcher
from .core.indexer import IndexWriter


def run_full_scan(cfg, repo: FileRepo) -> int:
    excludes: list = []
    for r in cfg.roots:
        if r.enabled:
            excludes.extend(r.excludes)
    scanner = Scanner(excludes=excludes, workers=cfg.scan_workers)
    roots = [r.path for r in cfg.roots if r.enabled]
    total = 0

    def on_batch(batch):
        nonlocal total
        repo.upsert_many(batch)
        total += len(batch)
        print(f"[scan] indexed {total}...", end="\r")

    t0 = time.time()
    scanner.scan_roots(roots, on_batch)
    print(f"\n[scan] done: {total} records in {time.time()-t0:.1f}s")
    return total


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="sakurafinder-daemon")
    ap.add_argument("--scan", action="store_true", help="启动时全量扫描")
    ap.add_argument("--no-watch", action="store_true", help="不启用实时监控")
    args = ap.parse_args(argv)

    cfg = load_config()
    if not cfg.roots:
        print("未配置索引根目录，请编辑 ~/.sakurafinder/config.json", file=sys.stderr)
        return 2

    db = Database(cfg.resolved_db_path(), enable_fts=cfg.enable_content_index)
    repo = FileRepo(db)

    if args.scan:
        run_full_scan(cfg, repo)

    if args.no_watch:
        return 0

    excludes: list = []
    for r in cfg.roots:
        if r.enabled:
            excludes.extend(r.excludes)
    watcher = Watcher(excludes=excludes)
    watcher.start([r.path for r in cfg.roots if r.enabled])

    writer = IndexWriter(repo, watcher)
    writer.start()

    stop = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    print("[daemon] watching... Ctrl+C to stop")
    while not stop.is_set():
        time.sleep(0.5)
    writer.stop()
    watcher.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())