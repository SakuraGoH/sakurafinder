# sakurafinder/search/parser.py
from __future__ import annotations
import re
from datetime import datetime
from typing import List
from ..models import SearchQuery, SizeFilter, TimeFilter

_UNITS = {"b": 1, "k": 1024, "m": 1024**2, "g": 1024**3, "t": 1024**4}


def _parse_size(s: str) -> SizeFilter:
    m = re.match(r"^(>=|<=|>|<|=)?\s*([\d.]+)\s*([bkmgt]?)b?$", s.strip(), re.I)
    if not m:
        raise ValueError(f"bad size: {s}")
    op = m.group(1) or "="
    val = float(m.group(2)) * _UNITS[(m.group(3) or "b").lower()]
    return SizeFilter(op=op, value=int(val))


def _parse_time(s: str) -> float:
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).timestamp()
        except ValueError:
            continue
    raise ValueError(f"bad time: {s}")


def parse(raw: str) -> SearchQuery:
    q = SearchQuery(raw=raw)
    if not raw.strip():
        return q
    q.use_regex = raw.startswith("re:")
    if q.use_regex:
        q.terms.append(raw[3:].strip())
        return q

    # 先按 | 分组做 OR，组内空格是 AND
    or_groups = [g.strip() for g in raw.split("|") if g.strip()]
    if len(or_groups) > 1:
        for g in or_groups:
            q.or_terms.append(g)
        # 简化处理：OR 组作为整体，交给 engine 处理
        q.terms = or_groups
        return q

    for tok in raw.split():
        if tok.startswith("-") and len(tok) > 1:
            q.not_terms.append(tok[1:])
        elif tok.lower().startswith("ext:"):
            q.exts = [e.strip().lstrip(".").lower()
                      for e in tok[4:].split(",") if e.strip()]
        elif tok.lower().startswith("size:"):
            q.size = _parse_size(tok[5:])
        elif tok.lower().startswith("after:"):
            t = q.time or TimeFilter()
            t.after = _parse_time(tok[6:])
            q.time = t
        elif tok.lower().startswith("before:"):
            t = q.time or TimeFilter()
            t.before = _parse_time(tok[7:])
            q.time = t
        elif tok.lower() == "dir:":
            q.dirs_only = True
        elif tok.lower() == "file:":
            q.files_only = True
        else:
            q.terms.append(tok)
    return q