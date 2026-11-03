# sakurafinder/ui/__init__.py
"""Qt 桌面 UI（PySide6）。

注意：本包**不在顶层 import**，只有显式进入 UI 时才拉起 Qt，
保证 daemon / CLI 在无 GUI 环境可用。
"""

from __future__ import annotations

__all__ = ["run_ui"]


def run_ui(argv: list[str] | None = None) -> int:
    """延迟导入，避免 `import sakurafinder.ui` 就拉 Qt 依赖。"""
    from .app import main as _main
    return _main(argv)