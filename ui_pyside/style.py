"""Gelir Hazırlama PySide6 görünümü — Teklif Hazırlama ile aynı renk ailesi."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap

PAGE_QSS = """
QWidget { font-family: 'Segoe UI'; font-size: 13px; color: #0f172a; }
QWidget#gelirRoot, QWidget#gelirBody, QScrollArea#gelirScroll { background: #f8fafc; }
QFrame#header { background: #ffffff; border: none; border-bottom: 1px solid #e2e8f0; }
QLabel#appTitle { font-size: 17px; font-weight: 600; }
QLabel#appSub { font-size: 12px; color: #64748b; }
QLabel#version { font-size: 11px; color: #64748b; background: #f1f5f9;
                 border: 1px solid #e2e8f0; border-radius: 9px; padding: 2px 8px; }

QFrame#card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; }
QLabel#stepNum { background: #2563eb; color: #ffffff; font-weight: 700; font-size: 12px;
                 border-radius: 11px; min-width: 22px; max-width: 22px;
                 min-height: 22px; max-height: 22px; qproperty-alignment: AlignCenter; }
QLabel#stepNum[tone="ok"] { background: #16a34a; }
QLabel#stepNum[tone="err"] { background: #dc2626; }
QLabel#stepTitle { font-size: 14px; font-weight: 600; }
QLabel#fieldLabel { color: #475569; }

QLabel#chip { border-radius: 6px; padding: 6px 10px; }
QLabel#chip[state="ok"] { color: #166534; background: #f0fdf4; border: 1px solid #bbf7d0; }
QLabel#chip[state="empty"] { color: #94a3b8; background: #f8fafc; border: 1px dashed #cbd5e1; }

QPushButton#fileBtn { padding: 6px 14px; font-weight: 600; border: 1px solid #cbd5e1;
                      border-radius: 6px; background: #ffffff; min-width: 84px; }
QPushButton#fileBtn:hover { background: #f1f5f9; border-color: #94a3b8; }
QPushButton#fileBtn:pressed { background: #e2e8f0; }
QPushButton#fileBtn:disabled { color: #94a3b8; }

QPushButton#primary { padding: 10px 16px; font-size: 14px; font-weight: 600;
                      border: 1px solid #1d4ed8; border-radius: 8px;
                      background: #2563eb; color: #ffffff; min-height: 24px; }
QPushButton#primary:hover { background: #1d4ed8; }
QPushButton#primary:pressed { background: #1e40af; }
QPushButton#primary:disabled { background: #bfdbfe; border-color: #bfdbfe; color: #ffffff; }

QPushButton#secondary { padding: 7px 14px; font-weight: 600; border: 1px solid #cbd5e1;
                        border-radius: 6px; background: #ffffff; }
QPushButton#secondary:hover { background: #f1f5f9; border-color: #94a3b8; }
QPushButton#link { border: none; background: transparent; color: #2563eb; font-weight: 600;
                   padding: 4px 2px; }
QPushButton#link:hover { color: #1d4ed8; text-decoration: underline; }
QPushButton#linkMuted { border: none; background: transparent; color: #64748b; padding: 4px 2px; }
QPushButton#linkMuted:hover { color: #dc2626; }

QComboBox, QLineEdit { padding: 6px 8px; border: 1px solid #cbd5e1; border-radius: 6px;
                       background: #ffffff; min-height: 20px; }
QComboBox:focus, QLineEdit:focus { border-color: #2563eb; }

QProgressBar { border: none; background: #e2e8f0; border-radius: 3px;
               max-height: 6px; min-height: 6px; }
QProgressBar::chunk { background: #2563eb; border-radius: 3px; }
QLabel#status { color: #475569; font-size: 12px; }

QFrame#tile { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; }
QFrame#tile[tone="warn"] { background: #fffbeb; border: 1px solid #fde68a; }
QLabel#tileNum { font-size: 20px; font-weight: 700; }
QLabel#tileNum[tone="warn"] { color: #92400e; }
QLabel#tileCap { font-size: 11px; color: #64748b; }
QLabel#tileCap[tone="warn"] { color: #92400e; }

QLabel#warnHead { color: #92400e; font-weight: 600; font-size: 12px; }
QLabel#warnRow { color: #334155; font-size: 12px; }
QLabel#note { color: #92400e; background: #fffbeb; border: 1px solid #fde68a;
              border-radius: 6px; padding: 6px 10px; font-size: 12px; }
QLabel#errText { color: #991b1b; background: #fef2f2; border: 1px solid #fecaca;
                 border-radius: 6px; padding: 8px 10px; }
QLabel#pathText { color: #475569; font-size: 12px; }

QPlainTextEdit#log { background: #0f172a; color: #e2e8f0; border: none; border-radius: 8px;
                     font-family: Consolas, 'Cascadia Mono', monospace; font-size: 12px;
                     padding: 8px; }
QScrollArea { border: none; }
QScrollArea#stbScroll, QWidget#stbHost { background: #ffffff; }

QPushButton#menuCard {
    text-align: left; padding: 18px 20px; border: 1px solid #e2e8f0;
    border-radius: 10px; background: #ffffff; min-height: 72px;
}
QPushButton#menuCard:hover { border-color: #2563eb; background: #f8fafc; }
QPushButton#menuCard:pressed { background: #eff6ff; }
QLabel#menuCardTitle { font-size: 15px; font-weight: 600; }
QLabel#menuCardSub { font-size: 12px; color: #64748b; }

QLabel#sonucOk { color: #166534; font-weight: 600; }
QLabel#sonucUyari { color: #92400e; font-weight: 600; }
QLabel#sonucYok { color: #991b1b; font-weight: 600; }
"""


def badge_pixmap(color: str, letter: str, size: int = 20) -> QPixmap:
    """Excel (yeşil X) / PDF (kırmızı P) rozetleri."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(1, 1, size - 2, size - 2, 3, 3)
    p.setPen(QColor("#ffffff"))
    font = QFont("Segoe UI", 9)
    font.setBold(True)
    p.setFont(font)
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, letter)
    p.end()
    return pm


def repolish(widget) -> None:
    """Dinamik özellik (state/tone) değişince QSS'in yeniden uygulanması için."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
