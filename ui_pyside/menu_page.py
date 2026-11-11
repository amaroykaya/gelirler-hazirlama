"""Ana menü — iş seçimi (Gelir Hazırlama / Fatura Tutar Kontrolü)."""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app_info import __version__
from ui.branding import make_pyside_logo_label
from ui_pyside.style import PAGE_QSS


def _label(text: str = "", name: Optional[str] = None) -> QLabel:
    w = QLabel(text)
    if name:
        w.setObjectName(name)
    return w


class MenuPage(QWidget):
    def __init__(
        self,
        on_gelir: Callable[[], None],
        on_tutar_kontrol: Callable[[], None],
    ) -> None:
        super().__init__()
        self.setObjectName("gelirRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(PAGE_QSS)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._build_header())

        body = QVBoxLayout()
        body.setContentsMargins(28, 28, 28, 28)
        body.setSpacing(16)

        body.addWidget(_label("Ne yapmak istiyorsunuz?", "stepTitle"))
        body.addWidget(
            _label("İşlemi seçin. Gelir hazırlama mevcut akışla aynı kalır.", "appSub")
        )
        body.addSpacing(8)

        body.addWidget(
            self._menu_card(
                "Gelir Hazırlama",
                "Satış faturaları + PDF → gelir kalemleri çalışma Excel'i",
                on_gelir,
            )
        )
        body.addWidget(
            self._menu_card(
                "Fatura Tutar Kontrolü",
                "Gelir kalemleri ↔ siparişler: KDV'siz tutar karşılaştırması",
                on_tutar_kontrol,
            )
        )
        body.addStretch(1)
        outer.addLayout(body, stretch=1)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("header")
        h = QHBoxLayout(header)
        h.setContentsMargins(22, 14, 22, 14)
        h.setSpacing(16)
        logo = make_pyside_logo_label(header=True, max_width=400)
        if logo is not None:
            pm = logo.pixmap()
            if pm is not None and not pm.isNull() and pm.height() > 40:
                logo.setPixmap(pm.scaledToHeight(40, Qt.TransformationMode.SmoothTransformation))
            h.addWidget(logo, alignment=Qt.AlignmentFlag.AlignVCenter)
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.VLine)
            sep.setStyleSheet("color: #e2e8f0;")
            h.addWidget(sep)
        titles = QVBoxLayout()
        titles.setSpacing(1)
        titles.addWidget(_label("Antsis Gelir Araçları", "appTitle"))
        titles.addWidget(_label("Gelir hazırlama ve fatura tutar kontrolü", "appSub"))
        h.addLayout(titles)
        h.addStretch(1)
        h.addWidget(_label(f"v{__version__}", "version"), alignment=Qt.AlignmentFlag.AlignTop)
        return header

    def _menu_card(self, title: str, subtitle: str, slot) -> QPushButton:
        btn = QPushButton()
        btn.setObjectName("menuCard")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QVBoxLayout(btn)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(4)
        t = _label(title, "menuCardTitle")
        s = _label(subtitle, "menuCardSub")
        t.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        s.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay.addWidget(t)
        lay.addWidget(s)
        btn.clicked.connect(slot)
        return btn
