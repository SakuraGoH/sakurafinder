# sakurafinder/config.py
from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List

DEFAULT_CONFIG_PATH = Path.home() / ".sakurafinder" / "config.json"


@dataclass
class RootDir:
    path: str
    enabled: bool = True
    # glob 风格排除规则，例如 ["**/node_modules/**", "**/.git/**"]
    excludes: List[str] = field(default_factory=list)


@dataclass
class Config:
    roots: List[RootDir] = field(default_factory=list)
    index_db: str = ""                # 留空则用默认位置
    enable_content_index: bool = False  # 是否启用 FTS5 全文索引
    max_content_size: int = 2 * 1024 * 1024  # 只索引小于 2MB 的文本
    scan_workers: int = 4
    debounce_ms: int = 120
    page_size: int = 500
    open_at_startup: bool = False
    hotkey: str = "Ctrl+Alt+Space"

    def resolved_db_path(self) -> Path:
        if self.index_db:
            return Path(self.index_db).expanduser()
        base = Path.home() / ".sakurafinder"
        base.mkdir(parents=True, exist_ok=True)
        return base / "index.db"


def load_config(path: Path | None = None) -> Config:
    p = path or DEFAULT_CONFIG_PATH
    if not p.exists():
        return Config()
    data = json.loads(p.read_text(encoding="utf-8"))
    roots = [RootDir(**r) for r in data.get("roots", [])]
    data["roots"] = roots
    return Config(**data)


def save_config(cfg: Config, path: Path | None = None) -> None:
    p = path or DEFAULT_CONFIG_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(cfg)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")