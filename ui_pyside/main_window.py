"""Antsis Gelir Araçları — bağımsız PySide6 penceresi (EXE / run_app.bat giriş noktası)."""

from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMainWindow

from app_info import app_window_title
from ui.branding import pyside_app_icon
from ui_pyside.menu_page import MenuPage
from ui_pyside.suite_page import GelirPage
from ui_pyside.tutar_kontrol_page import TutarKontrolPage


class GelirMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(app_window_title())
        icon = pyside_app_icon()
        if icon is not None:
            self.setWindowIcon(icon)
        self.setMinimumSize(620, 560)
        self.resize(720, 820)
        self.show_menu()

    def show_menu(self) -> None:
        self.setCentralWidget(
            MenuPage(
                on_gelir=self.show_gelir,
                on_tutar_kontrol=self.show_tutar_kontrol,
            )
        )

    def show_gelir(self) -> None:
        self.setCentralWidget(GelirPage(on_back=self.show_menu))

    def show_tutar_kontrol(self) -> None:
        self.setCentralWidget(TutarKontrolPage(on_back=self.show_menu))


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
