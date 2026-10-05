"""Gelir Hazırlama — bağımsız PySide6 penceresi (EXE / run_app.bat giriş noktası)."""

from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMainWindow

from app_info import app_window_title
from ui.branding import pyside_app_icon
from ui_pyside.suite_page import GelirPage


class GelirMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(app_window_title())
        icon = pyside_app_icon()
        if icon is not None:
            self.setWindowIcon(icon)
        self.setCentralWidget(GelirPage())
        self.setMinimumSize(620, 560)
        self.resize(720, 820)


def run_app() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    icon = pyside_app_icon()
    if icon is not None:
        app.setWindowIcon(icon)
    win = GelirMainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_app())
