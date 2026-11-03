# sakurafinder/__init__.py
"""SakuraFinder —— 跨平台文件索引与搜索工具（Everything 的 Python 替代品）。

顶层只暴露稳定、常用的入口，方便：

    import sakurafinder
    svc = sakurafinder.SearchService(sakurafinder.load_config())
    res = svc.search("report ext:pdf")
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "Config", "RootDir", "load_config", "save_config",
    "FileRecord", "SearchQuery", "SearchResult",
    "SearchService",
]

from .config import Config, RootDir, load_config, save_config
from .models import FileRecord, SearchQuery, SearchResult
from .api.service import SearchService