# sakurafinder/models.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Literal


@dataclass
class FileRecord:
    path: str
    name: str
    ext: str
    size: int
    ctime: float
    mtime: float
    atime: float
    is_dir: bool
    is_hidden: bool = False
    is_readonly: bool = False


@dataclass
class SizeFilter:
    op: Literal[">", ">=", "<", "<=", "="] = ">"
    value: int = 0


@dataclass
class TimeFilter:
    field: Literal["mtime", "ctime", "atime"] = "mtime"
    after: Optional[float] = None
    before: Optional[float] = None


@dataclass
class SearchQuery:
    raw: str = ""                       # 用户原始输入
    terms: List[str] = field(default_factory=list)   # 已解析的 AND 词
    or_terms: List[str] = field(default_factory=list)
    not_terms: List[str] = field(default_factory=list)
    use_regex: bool = False
    size: Optional[SizeFilter] = None
    time: Optional[TimeFilter] = None
    exts: List[str] = field(default_factory=list)
    dirs_only: bool = False
    files_only: bool = False
    sort_by: Literal["name", "path", "size", "mtime"] = "name"
    sort_desc: bool = False
    limit: int = 500
    offset: int = 0


@dataclass
class SearchResult:
    items: List[FileRecord]
    total: int
    elapsed_ms: float