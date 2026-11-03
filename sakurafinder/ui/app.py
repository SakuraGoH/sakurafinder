# sakurafinder/ui/app.py
from __future__ import annotations
import sys
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from .main_window import MainWindow


def main(argv=None) -> int:
    argv = argv or sys.argv
    app = QApplication(argv)
    app.setApplicationName("SakuraFinder")
    app.setQuitOnLastWindowClosed(False)  # 托盘常驻

    win = MainWindow()
    win.show()

    tray = QSystemTrayIcon(QIcon.fromTheme("system-search"), app)
    menu = QMenu()
    a_show = QAction("显示窗口", app)
    a_show.triggered.connect(win._focus_search)
    a_quit = QAction("退出", app)
    a_quit.triggered.connect(app.quit)
    menu.addAction(a_show)
    menu.addSeparator()
    menu.addAction(a_quit)
    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason: win._focus_search()
                           if reason == QSystemTrayIcon.Trigger else None)
    tray.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())