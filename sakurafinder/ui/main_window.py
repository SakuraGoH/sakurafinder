# sakurafinder/ui/main_window.py
from __future__ import annotations
import os
import subprocess
import sys
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow, QLineEdit, QTableView, QVBoxLayout, QWidget,
    QMenu, QApplication, QHeaderView, QLabel,
)
from ..config import load_config
from ..api.service import SearchService
from .result_model import ResultModel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SakuraFinder")
        self.resize(1000, 640)

        self.cfg = load_config()
        self.svc = SearchService(self.cfg)
        self.model = ResultModel()

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("输入搜索词（空格=AND，-排除，ext:py，size:>1MB，re:正则）")
        self.search_box.setClearButtonEnabled(True)
        layout.addWidget(self.search_box)

        self.status = QLabel("")
        layout.addWidget(self.status)

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.ExtendedSelection)
        self.table.setSortingEnabled(False)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_context_menu)
        self.table.doubleClicked.connect(self._on_double_click)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        self.setCentralWidget(central)

        # 防抖
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(self.cfg.debounce_ms)
        self._debounce.timeout.connect(self._do_search)
        self.search_box.textChanged.connect(lambda _: self._debounce.start())
        self.search_box.returnPressed.connect(self._do_search)

        # 全局快捷键（窗口内）：Ctrl+L 聚焦搜索框
        act = QAction(self)
        act.setShortcut(QKeySequence("Ctrl+L"))
        act.triggered.connect(self._focus_search)
        self.addAction(act)

    def _focus_search(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.search_box.setFocus()

    def _do_search(self):
        raw = self.search_box.text()
        res = self.svc.search(raw, limit=self.cfg.page_size)
        self.model.set_rows(res.items)
        self.status.setText(f"{res.total} 条结果 · {res.elapsed_ms:.1f} ms")

    def _selected_records(self):
        rows = {i.row() for i in self.table.selectionModel().selectedRows()}
        return [self.model.record_at(r) for r in sorted(rows)]

    def _on_double_click(self, index):
        rec = self.model.record_at(index.row())
        self._open_path(rec.path)

    def _open_path(self, path: str) -> None:
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            self.status.setText(f"打开失败: {e}")

    def _reveal(self, path: str) -> None:
        try:
            if sys.platform.startswith("win"):
                subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", path])
            else:
                subprocess.Popen(["xdg-open", os.path.dirname(path)])
        except Exception as e:
            self.status.setText(f"定位失败: {e}")

    def _on_context_menu(self, pos):
        recs = self._selected_records()
        if not recs:
            return
        menu = QMenu(self)
        a_open = menu.addAction("打开")
        a_reveal = menu.addAction("打开所在目录")
        a_copy = menu.addAction("复制路径")
        menu.addSeparator()
        a_del = menu.addAction("删除（进回收站）")
        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
        if chosen == a_open:
            for r in recs:
                self._open_path(r.path)
        elif chosen == a_reveal:
            self._reveal(recs[0].path)
        elif chosen == a_copy:
            QApplication.clipboard().setText("\n".join(r.path for r in recs))
            self.status.setText(f"已复制 {len(recs)} 条路径")
        elif chosen == a_del:
            self._delete(recs)

    def _delete(self, recs):
        try:
            from send2trash import send2trash
        except ImportError:
            self.status.setText("删除需要安装 send2trash")
            return
        failed = []
        for r in recs:
            try:
                send2trash(r.path)
            except Exception:
                failed.append(r.path)
        if failed:
            self.status.setText(f"{len(failed)} 项删除失败")
        else:
            self._do_search()