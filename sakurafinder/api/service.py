# sakurafinder/api/service.py
from __future__ import annotations
from typing import Optional
from ..config import Config
from ..storage.db import Database
from ..storage.repo import FileRepo
from ..search.parser import parse
from ..search.engine import SearchEngine
from ..models import SearchResult


class SearchService:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.db = Database(cfg.resolved_db_path(),
                           enable_fts=cfg.enable_content_index)
        self.repo = FileRepo(self.db)
        self.engine = SearchEngine(self.repo)

    def search(self, raw: str, limit: int = 500, offset: int = 0,
               sort_by: str = "name", sort_desc: bool = False) -> SearchResult:
        q = parse(raw)
        q.limit, q.offset = limit, offset
        q.sort_by, q.sort_desc = sort_by, sort_desc  # type: ignore
        return self.engine.search(q)

    def stats(self) -> dict:
        return {"total_files": self.repo.count()}