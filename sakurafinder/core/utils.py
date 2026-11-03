# sakurafinder/core/utils.py
from __future__ import annotations
import fnmatch
import os
from pathlib import Path
from typing import Iterable, List


def normalize_path(p: str) -> str:
    # 统一分隔符 / 去掉尾部分隔符；Windows 长路径加 \\?\ 前缀
    p = os.path.normpath(p)
    if os.name == "nt" and len(p) >= 260 and not p.startswith("\\\\?\\"):
        p = "\\\\?\\" + os.path.abspath(p)
    return p


def should_exclude(path: str, excludes: List[str]) -> bool:
    if not excludes:
        return False
    # 统一成 / 方便匹配
    norm = path.replace("\\", "/")
    for pat in excludes:
        if fnmatch.fnmatch(norm, pat) or fnmatch.fnmatch(norm + "/", pat):
            return True
        # 支持 "目录名/**" 这种前缀匹配
        prefix = pat.rstrip("*").rstrip("/")
        if prefix and norm.startswith(prefix + "/"):
            return True
    return False


def is_hidden(path: str) -> bool:
    name = os.path.basename(path)
    if os.name == "nt":
        try:
            import ctypes
            attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
            return attrs != -1 and bool(attrs & 0x2)
        except Exception:
            return name.startswith(".")
    return name.startswith(".")