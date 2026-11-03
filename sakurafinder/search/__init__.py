# sakurafinder/search/__init__.py
"""查询层：语法解析、SQL 翻译、排序打分。"""
from __future__ import annotations

__all__ = ["parse", "SearchEngine"]

from .parser import parse
from .engine import SearchEngine