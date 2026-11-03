# sakurafinder/cli.py
from __future__ import annotations
import argparse
import sys
from .config import load_config
from .api.service import SearchService


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="sakurafinder")
    ap.add_argument("query", nargs="?", default="", help="搜索词")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--sort", default="name",
                    choices=["name", "path", "size", "mtime"])
    ap.add_argument("--desc", action="store_true")
    args = ap.parse_args(argv)

    svc = SearchService(load_config())
    res = svc.search(args.query, limit=args.limit, offset=args.offset,
                     sort_by=args.sort, sort_desc=args.desc)
    print(f"# {res.total} results, {res.elapsed_ms:.1f}ms")
    for r in res.items:
        print(r.path)
    return 0


if __name__ == "__main__":
    sys.exit(main())