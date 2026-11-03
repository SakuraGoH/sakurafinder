# sakurafinder/search/engine.py
from __future__ import annotations
import re
import time
from typing import List, Tuple
from ..models import SearchQuery, SearchResult, FileRecord
from ..storage.repo import FileRepo

_LIKE_ESCAPE = {"%": "\\%", "_": "\\_"}


def _escape_like(s: str) -> str:
    for k, v in _LIKE_ESCAPE.items():
        s = s.replace(k, v)
    return s


def _term_to_sql(term: str) -> Tuple[str, list]:
    # 有通配符 -> LIKE；否则用 INSTR 更直观（也能命中子串）
    if "*" in term or "?" in term:
        pat = term.replace("*", "%").replace("?", "_")
        return "(name LIKE ? ESCAPE '\\' OR path LIKE ? ESCAPE '\\')", \
               [f"%{_escape_like(pat)}%", f"%{_escape_like(pat)}%"]
    return "(INSTR(lower(name), lower(?)) > 0 OR INSTR(lower(path), lower(?)) > 0)", \
           [term, term]


def build_where(q: SearchQuery) -> Tuple[str, list]:
    clauses: List[str] = []
    params: list = []

    if q.terms and not q.or_terms:
        for t in q.terms:
            c, p = _term_to_sql(t)
            clauses.append(c)
            params.extend(p)
    elif q.or_terms:
        or_clauses = []
        for g in q.or_terms:
            inner = []
            inner_p = []
            for t in g.split():
                c, p = _term_to_sql(t)
                inner.append(c)
                inner_p.extend(p)
            if inner:
                or_clauses.append("(" + " AND ".join(inner) + ")")
                params.extend(inner_p)
        if or_clauses:
            clauses.append("(" + " OR ".join(or_clauses) + ")")

    for t in q.not_terms:
        c, p = _term_to_sql(t)
        clauses.append(f"NOT {c}")
        params.extend(p)

    if q.exts:
        placeholders = ",".join("?" * len(q.exts))
        clauses.append(f"ext IN ({placeholders})")
        params.extend(q.exts)

    if q.size:
        op = q.size.op
        clauses.append(f"size {op} ?")
        params.append(q.size.value)

    if q.time:
        if q.time.after is not None:
            clauses.append(f"{q.time.field} >= ?")
            params.append(q.time.after)
        if q.time.before is not None:
            clauses.append(f"{q.time.field} <= ?")
            params.append(q.time.before)

    if q.dirs_only:
        clauses.append("is_dir = 1")
    if q.files_only:
        clauses.append("is_dir = 0")

    where = " AND ".join(clauses) if clauses else "1=1"
    return where, params


def build_order(q: SearchQuery) -> str:
    col = {"name": "name", "path": "path", "size": "size", "mtime": "mtime"}[q.sort_by]
    direction = "DESC" if q.sort_desc else "ASC"
    return f"{col} COLLATE NOCASE {direction}"


class SearchEngine:
    def __init__(self, repo: FileRepo):
        self.repo = repo

    def search(self, q: SearchQuery) -> SearchResult:
        t0 = time.perf_counter()
        where, params = build_where(q)
        order = build_order(q)

        # 正则 / 相关性重排：先取较大候选集，再 Python 后过滤
        if q.use_regex and q.terms:
            pattern = re.compile(q.terms[0])
            items, total = self.repo.search_sql(where, params, order,
                                                 limit=5000, offset=0)
            matched = [r for r in items if pattern.search(r.name) or pattern.search(r.path)]
            total = len(matched)
            page = matched[q.offset:q.offset + q.limit]
        else:
            page, total = self.repo.search_sql(where, params, order,
                                               q.limit, q.offset)

        elapsed = (time.perf_counter() - t0) * 1000
        return SearchResult(items=page, total=total, elapsed_ms=elapsed)