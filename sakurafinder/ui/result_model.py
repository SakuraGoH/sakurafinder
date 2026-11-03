# sakurafinder/ui/result_model.py
from __future__ import annotations
from typing import List
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from ..models import FileRecord


class ResultModel(QAbstractTableModel):
    HEADERS = ["名称", "路径", "大小", "修改时间"]

    def __init__(self):
        super().__init__()
        self._rows: List[FileRecord] = []

    def set_rows(self, rows: List[FileRecord]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        r = self._rows[index.row()]
        col = index.column()
        if col == 0:
            return r.name
        if col == 1:
            return r.path
        if col == 2:
            return self._fmt_size(r.size)
        if col == 3:
            import datetime
            return datetime.datetime.fromtimestamp(r.mtime).strftime("%Y-%m-%d %H:%M")
        return None

    def record_at(self, row: int) -> FileRecord:
        return self._rows[row]

    @staticmethod
    def _fmt_size(n: int) -> str:
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if n < 1024:
                return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} PB"