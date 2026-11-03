# sakurafinder/api/__init__.py
"""对外查询服务。UI / CLI / HTTP 都通过这里复用同一入口。"""
from __future__ import annotations

__all__ = ["SearchService"]

from .service import SearchService