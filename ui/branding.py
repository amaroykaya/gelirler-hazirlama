"""Uygulama markası: logo yolları ve UI yardımcıları."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path

from app_info import APP_NAME


def _app_root() -> Path:
    """Geliştirmede repo kökü; PyInstaller exe'te _MEIPASS."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


BRANDING_DIR = _app_root() / "assets" / "branding"
LOGO_PNG = BRANDING_DIR / "antsis_logo.png"
LOGO_HEADER_PNG = BRANDING_DIR / "antsis_logo_header.png"
LOGO_ICO = BRANDING_DIR / "antsis_logo.ico"


def _logo_path(*, header: bool = True) -> Path | None:
    if header and LOGO_HEADER_PNG.exists():
        return LOGO_HEADER_PNG
    if LOGO_PNG.exists():
        return LOGO_PNG
    return None


def apply_tk_window_icon(root: tk.Misc) -> None:
    if not LOGO_ICO.exists():
        return
    try:
        root.iconbitmap(str(LOGO_ICO))
    except tk.TclError:
        pass


def load_tk_logo(master: tk.Misc, *, header: bool = True, max_width: int = 180) -> tk.PhotoImage | None:
    path = _logo_path(header=header)
    if path is None:
        return None

    image = tk.PhotoImage(master=master, file=str(path))
    if image.width() > max_width:
        factor = max(1, round(image.width() / max_width))
        image = image.subsample(factor, factor)
    return image


def make_pyside_logo_label(*, header: bool = True, max_width: int = 200):
    """PySide6 logo etiketi; PySide6 yoksa None döner."""
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QPixmap
        from PySide6.QtWidgets import QLabel
    except ImportError:
        return None

    label = QLabel()
    path = _logo_path(header=header)
    if path is None:
        label.setText(APP_NAME)
        return label

    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        label.setText(APP_NAME)
        return label

    if pixmap.width() > max_width:
        pixmap = pixmap.scaledToWidth(max_width, Qt.TransformationMode.SmoothTransformation)
    label.setPixmap(pixmap)
    label.setScaledContents(False)
    return label


def pyside_app_icon():
    try:
        from PySide6.QtGui import QIcon
    except ImportError:
        return None

    if LOGO_ICO.exists():
        return QIcon(str(LOGO_ICO))
    if LOGO_PNG.exists():
        return QIcon(str(LOGO_PNG))
    return QIcon()
