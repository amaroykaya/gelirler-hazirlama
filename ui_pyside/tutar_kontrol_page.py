"""Fatura tutar kontrolü — PySide6 sayfası (gelir akışından bağımsız)."""

from __future__ import annotations

import subprocess
import traceback
from pathlib import Path
from typing import Callable, List, Optional

from PySide6.QtCore import QObject, QSettings, Qt, QThread, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app_info import __version__
from fatura_tutar_kontrol import FaturaKontrolSatir, run_fatura_tutar_kontrol
from ui.branding import make_pyside_logo_label
from ui_pyside.style import PAGE_QSS, badge_pixmap, repolish

_LISTE_LIMIT = 50


def _label(text: str = "", name: Optional[str] = None) -> QLabel:
    w = QLabel(text)
    if name:
        w.setObjectName(name)
    return w


def _fmt_usd(v: Optional[float]) -> str:
    if v is None:
        return "—"
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


class _Card(QFrame):
    def __init__(self, step: str, title: str) -> None:
        super().__init__()
        self.setObjectName("card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(18, 14, 18, 16)
        self.body.setSpacing(12)
        head = QHBoxLayout()
        head.setSpacing(10)
        self.step = _label(step, "stepNum")
        self.title = _label(title, "stepTitle")
        head.addWidget(self.step)
        head.addWidget(self.title)
        head.addStretch(1)
        self.body.addLayout(head)

    def set_head(self, step: str, title: str, tone: str = "") -> None:
        self.step.setText(step)
        self.title.setText(title)
        self.step.setProperty("tone", tone)
        repolish(self.step)


class _Tile(QFrame):
    def __init__(self, caption: str) -> None:
        super().__init__()
        self.setObjectName("tile")
        v = QVBoxLayout(self)
        v.setContentsMargins(14, 10, 14, 10)
        v.setSpacing(0)
        self.num = _label("", "tileNum")
        self.cap = _label(caption, "tileCap")
        v.addWidget(self.num)
        v.addWidget(self.cap)

    def set_value(self, value: str, caption: Optional[str] = None, warn: bool = False) -> None:
        self.num.setText(value)
        if caption is not None:
            self.cap.setText(caption)
        tone = "warn" if warn else ""
        for w in (self, self.num, self.cap):
            w.setProperty("tone", tone)
            repolish(w)


class _Worker(QObject):
    finished_ok = Signal(str, object, object)  # path, rows, stats
    finished_err = Signal(str)

    def __init__(self, gelir: str, siparis: str, output_folder: str) -> None:
        super().__init__()
        self._gelir = gelir
        self._siparis = siparis
        self._output_folder = output_folder

    @Slot()
    def run(self) -> None:
        try:
            path, rows, stats = run_fatura_tutar_kontrol(
                self._gelir, self._siparis, self._output_folder
            )
            self.finished_ok.emit(path, rows, stats)
        except Exception as exc:  # noqa: BLE001
            self.finished_err.emit(f"{exc}\n\n{traceback.format_exc()}")


class TutarKontrolPage(QWidget):
    def __init__(self, on_back: Optional[Callable[[], None]] = None) -> None:
        super().__init__()
        self.setObjectName("gelirRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(PAGE_QSS)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._on_back = on_back
        self._settings = QSettings("Antsis", "FaturaTutarKontrol")
        self._gelir_path = ""
        self._siparis_path = ""
        self._output_dir = ""
        self._last_output_path = ""
        self._thread: QThread | None = None
        self._worker: _Worker | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._build_header())

        scroll = QScrollArea()
        scroll.setObjectName("gelirScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body_host = QWidget()
        body_host.setObjectName("gelirBody")
        body = QVBoxLayout(body_host)
        body.setContentsMargins(22, 18, 22, 20)
        body.setSpacing(14)
        scroll.setWidget(body_host)
        outer.addWidget(scroll, stretch=1)

        body.addWidget(self._build_inputs_card())
        body.addWidget(self._build_output_card())

        self._run_btn = QPushButton("Kontrol Et")
        self._run_btn.setObjectName("primary")
        self._run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._run_btn.clicked.connect(self._on_run)
        body.addWidget(self._run_btn)

        self._progress = QProgressBar()
        self._progress.setTextVisible(False)
        self._progress.setRange(0, 0)
        self._progress.hide()
        body.addWidget(self._progress)

        self._status = _label("", "status")
        self._status.setWordWrap(True)
        body.addWidget(self._status)

        self._result = self._build_result_card()
        self._result.hide()
        body.addWidget(self._result)

        self._log = QPlainTextEdit()
        self._log.setObjectName("log")
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(160)
        self._log.hide()
        body.addWidget(self._log)

        body.addStretch(1)
        self._refresh_ready()

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
        titles.addWidget(_label("Fatura Tutar Kontrolü", "appTitle"))
        titles.addWidget(
            _label("Gelir kalemleri ↔ siparişler (KDV'siz dolar)", "appSub")
        )
        h.addLayout(titles)
        h.addStretch(1)
        if self._on_back is not None:
            back = QPushButton("← Ana Menü")
            back.setObjectName("link")
            back.setCursor(Qt.CursorShape.PointingHandCursor)
            back.clicked.connect(self._on_back)
            h.addWidget(back, alignment=Qt.AlignmentFlag.AlignTop)
        h.addWidget(_label(f"v{__version__}", "version"), alignment=Qt.AlignmentFlag.AlignTop)
        return header

    def _grid(self) -> QGridLayout:
        g = QGridLayout()
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(10)
        g.setColumnMinimumWidth(0, 22)
        g.setColumnMinimumWidth(1, 120)
        g.setColumnStretch(2, 1)
        return g

    def _chip(self) -> QLabel:
        chip = _label("", "chip")
        chip.setMinimumWidth(120)
        chip.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        return chip

    def _file_btn(self, slot) -> QPushButton:
        b = QPushButton("Seç…")
        b.setObjectName("fileBtn")
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.clicked.connect(slot)
        return b

    def _set_chip(self, chip: QLabel, text: str, *, empty_text: str = "Seçilmedi", tooltip: str = "") -> None:
        if text:
            chip.setProperty("state", "ok")
            elided = chip.fontMetrics().elidedText(text, Qt.TextElideMode.ElideMiddle, 420)
            chip.setText(f"✓  {elided}")
            chip.setToolTip(tooltip or text)
        else:
            chip.setProperty("state", "empty")
            chip.setText(empty_text)
            chip.setToolTip("")
        repolish(chip)

    def _build_inputs_card(self) -> _Card:
        card = _Card("1", "Excel dosyaları")
        g = self._grid()

        sat_icon = QLabel()
        sat_icon.setPixmap(badge_pixmap("#217346", "X"))
        g.addWidget(sat_icon, 0, 0)
        g.addWidget(_label("Gelir kalemleri", "fieldLabel"), 0, 1)
        self._gelir_chip = self._chip()
        g.addWidget(self._gelir_chip, 0, 2)
        self._gelir_btn = self._file_btn(self._pick_gelir)
        g.addWidget(self._gelir_btn, 0, 3)

        sip_icon = QLabel()
        sip_icon.setPixmap(badge_pixmap("#2563eb", "S"))
        g.addWidget(sip_icon, 1, 0)
        g.addWidget(_label("Siparişler", "fieldLabel"), 1, 1)
        self._siparis_chip = self._chip()
        g.addWidget(self._siparis_chip, 1, 2)
        self._siparis_btn = self._file_btn(self._pick_siparis)
        g.addWidget(self._siparis_btn, 1, 3)

        card.body.addLayout(g)
        self._set_chip(self._gelir_chip, "", empty_text="gelir_kalemleri_….xlsx")
        self._set_chip(self._siparis_chip, "")
        return card

    def _build_output_card(self) -> _Card:
        card = _Card("2", "Çıktı")
        g = self._grid()
        g.addWidget(_label("Çıktı klasörü", "fieldLabel"), 0, 1)
        self._out_chip = self._chip()
        g.addWidget(self._out_chip, 0, 2)
        self._out_btn = self._file_btn(self._pick_output)
        g.addWidget(self._out_btn, 0, 3)
        card.body.addLayout(g)
        self._set_chip(self._out_chip, "")
        return card

    def _build_result_card(self) -> _Card:
        card = _Card("✓", "Sonuç")
        self._tiles_row = QWidget()
        tiles = QHBoxLayout(self._tiles_row)
        tiles.setContentsMargins(0, 0, 0, 0)
        tiles.setSpacing(10)
        self._tile_toplam = _Tile("fatura kontrol")
        self._tile_ok = _Tile("OK")
        self._tile_uyari = _Tile("uyarı (fark)")
        self._tile_yok = _Tile("siparişte yok")
        for t in (self._tile_toplam, self._tile_ok, self._tile_uyari, self._tile_yok):
            tiles.addWidget(t)
        card.body.addWidget(self._tiles_row)

        self._err_text = _label("", "errText")
        self._err_text.setWordWrap(True)
        self._err_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        card.body.addWidget(self._err_text)

        self._list_box = QWidget()
        lv = QVBoxLayout(self._list_box)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(4)
        lv.addWidget(
            _label(
                "Uyarı ve yok listesi — Gelir KDV'siz $ ↔ Sipariş Toplam Fiyat (toplam)",
                "warnHead",
            )
        )
        self._list_scroll = QScrollArea()
        self._list_scroll.setWidgetResizable(True)
        self._list_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._list_scroll.setObjectName("stbScroll")
        self._list_host = QWidget()
        self._list_host.setObjectName("stbHost")
        self._list_layout = QVBoxLayout(self._list_host)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(4)
        self._list_scroll.setWidget(self._list_host)
        lv.addWidget(self._list_scroll)
        card.body.addWidget(self._list_box)

        self._path_label = _label("", "pathText")
        self._path_label.setWordWrap(True)
        self._path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        card.body.addWidget(self._path_label)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self._open_excel_btn = QPushButton("Excel'i Aç")
        self._open_excel_btn.setObjectName("secondary")
        self._open_excel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_excel_btn.clicked.connect(self._open_excel)
        self._open_dir_btn = QPushButton("Klasörü Aç")
        self._open_dir_btn.setObjectName("secondary")
        self._open_dir_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_dir_btn.clicked.connect(self._open_folder)
        self._log_btn = QPushButton("Ayrıntılı listeyi göster  ▸")
        self._log_btn.setObjectName("link")
        self._log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._log_btn.clicked.connect(self._toggle_log)
        actions.addWidget(self._open_excel_btn)
        actions.addWidget(self._open_dir_btn)
        actions.addStretch(1)
        actions.addWidget(self._log_btn)
        card.body.addLayout(actions)
        return card

    def _start_dir(self, key: str) -> str:
        d = self._settings.value(key, "", type=str)
        return d if d and Path(d).is_dir() else ""

    def _remember_dir(self, key: str, path: str) -> None:
        p = Path(path)
        self._settings.setValue(key, str(p if p.is_dir() else p.parent))

    def _set_status(self, text: str) -> None:
        self._status.setText(text)
        self._status.setVisible(bool(text))

    def _refresh_ready(self) -> None:
        busy = self._thread is not None and self._thread.isRunning()
        ready = bool(self._gelir_path and self._siparis_path and self._output_dir)
        self._run_btn.setEnabled(ready and not busy)
        if busy:
            return
        if not self._gelir_path:
            self._set_status("Gelir kalemleri Excel'ini seçin (gelir_kalemleri_….xlsx).")
        elif not self._siparis_path:
            self._set_status("Siparişler Excel'ini seçin.")
        elif not self._output_dir:
            self._set_status("Kontrol çıktısının kaydedileceği klasörü seçin.")
        else:
            self._set_status("")

    def _set_busy(self, busy: bool) -> None:
        for w in (self._gelir_btn, self._siparis_btn, self._out_btn):
            w.setEnabled(not busy)
        self._progress.setVisible(busy)
        self._run_btn.setText("Kontrol ediliyor…" if busy else "Kontrol Et")
        self._refresh_ready()

    def _pick_gelir(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Gelir kalemleri Excel'ini seçin",
            self._start_dir("dir/gelir"),
            "Excel (*.xlsx *.xls);;Tüm dosyalar (*.*)",
        )
        if not path:
            return
        self._gelir_path = path
        self._remember_dir("dir/gelir", path)
        self._set_chip(self._gelir_chip, Path(path).name, tooltip=path)
        self._gelir_btn.setText("Değiştir")
        self._refresh_ready()

    def _pick_siparis(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Siparişler Excel'ini seçin",
            self._start_dir("dir/siparis"),
            "Excel (*.xlsx *.xls);;Tüm dosyalar (*.*)",
        )
        if not path:
            return
        self._siparis_path = path
        self._remember_dir("dir/siparis", path)
        self._set_chip(self._siparis_chip, Path(path).name, tooltip=path)
        self._siparis_btn.setText("Değiştir")
        self._refresh_ready()

    def _pick_output(self) -> None:
        d = QFileDialog.getExistingDirectory(
            self, "Çıktı klasörünü seçin", self._start_dir("dir/output")
        )
        if not d:
            return
        self._output_dir = d
        self._remember_dir("dir/output", d)
        self._set_chip(self._out_chip, d, tooltip=d)
        self._out_btn.setText("Değiştir")
        self._refresh_ready()

    def _on_run(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            return
        if not Path(self._gelir_path).is_file():
            QMessageBox.warning(self, "Fatura tutar kontrolü", "Gelir kalemleri Excel bulunamadı.")
            return
        if not Path(self._siparis_path).is_file():
            QMessageBox.warning(self, "Fatura tutar kontrolü", "Sipariş Excel bulunamadı.")
            return
        if not Path(self._output_dir).is_dir():
            QMessageBox.warning(self, "Fatura tutar kontrolü", "Çıktı klasörü bulunamadı.")
            return

        self._result.hide()
        self._log.clear()
        self._set_status("Karşılaştırılıyor ve Excel kaydediliyor…")

        self._thread = QThread(self)
        self._worker = _Worker(self._gelir_path, self._siparis_path, self._output_dir)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished_ok.connect(self._on_ok)
        self._worker.finished_err.connect(self._on_err)
        self._worker.finished_ok.connect(self._thread.quit)
        self._worker.finished_err.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)
        self._thread.start()
        self._set_busy(True)

    @Slot(str, object, object)
    def _on_ok(self, path: str, rows: object, stats: object) -> None:
        rows_list: List[FaturaKontrolSatir] = list(rows) if rows else []
        st = stats if isinstance(stats, dict) else {}
        self._last_output_path = path
        self._result.set_head("✓", "Sonuç", tone="ok")
        self._tiles_row.show()
        self._err_text.hide()
        self._open_excel_btn.show()
        self._open_dir_btn.show()

        self._tile_toplam.set_value(str(st.get("toplam", len(rows_list))))
        self._tile_ok.set_value(str(st.get("ok", 0)))
        self._tile_uyari.set_value(
            str(st.get("uyari", 0)), "uyarı (fark)", warn=int(st.get("uyari", 0) or 0) > 0
        )
        self._tile_yok.set_value(
            str(st.get("yok", 0)), "siparişte yok", warn=int(st.get("yok", 0) or 0) > 0
        )

        problem = [r for r in rows_list if r.sonuc != "OK"]
        self._fill_problem_list(problem)
        self._fill_log(rows_list, st)
        self._path_label.setText(f"Kaydedildi: {Path(path).name}")
        self._path_label.setToolTip(path)
        self._result.show()
        self._set_status("")

    def _fill_problem_list(self, rows: List[FaturaKontrolSatir]) -> None:
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not rows:
            self._list_box.hide()
            return
        for r in rows[:_LISTE_LIMIT]:
            if r.sonuc == "YOK":
                name = "sonucYok"
                detail = f"siparişte yok — gelir KDV'siz {_fmt_usd(r.satis_kdv_siz)}"
            else:
                name = "sonucUyari"
                detail = (
                    f"gelir {_fmt_usd(r.satis_kdv_siz)} / sipariş {_fmt_usd(r.siparis_toplam)} "
                    f"/ fark {_fmt_usd(r.fark)}"
                )
            lbl = _label(f"•  {r.fatura_no}  {r.firma} — {detail}", name)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._list_layout.addWidget(lbl)
        if len(rows) > _LISTE_LIMIT:
            self._list_layout.addWidget(
                _label(f"… ve {len(rows) - _LISTE_LIMIT} satır daha (ayrıntılı listede)", "warnRow")
            )
        shown = min(len(rows), _LISTE_LIMIT) + (1 if len(rows) > _LISTE_LIMIT else 0)
        self._list_scroll.setFixedHeight(min(shown, 10) * 22 + 4)
        self._list_box.show()

    def _fill_log(self, rows: List[FaturaKontrolSatir], st: dict) -> None:
        lines = [
            f"Kontrol edilen fatura: {st.get('toplam', 0)}",
            f"OK: {st.get('ok', 0)}  |  Uyarı: {st.get('uyari', 0)}  |  Yok: {st.get('yok', 0)}",
            f"Siparişte benzersiz fatura no: {st.get('siparis_fatura_no', 0)}",
            "",
            f"{'Sonuç':<8} {'Fatura No':<24} {'Firma':<14} {'Gelir':>12} {'Sipariş':>12} {'Fark':>12}",
            "-" * 90,
        ]
        for r in rows:
            lines.append(
                f"{r.sonuc:<8} {r.fatura_no:<24} {(r.firma or '')[:14]:<14} "
                f"{_fmt_usd(r.satis_kdv_siz):>12} {_fmt_usd(r.siparis_toplam):>12} {_fmt_usd(r.fark):>12}"
            )
        self._log.setPlainText("\n".join(lines))

    @Slot(str)
    def _on_err(self, msg: str) -> None:
        self._result.set_head("!", "Kontrol tamamlanamadı", tone="err")
        self._tiles_row.hide()
        self._list_box.hide()
        self._path_label.setText("")
        self._open_excel_btn.hide()
        self._open_dir_btn.hide()
        short = msg.split("\n\n", 1)[0].strip()
        self._err_text.setText(short or "Bilinmeyen hata.")
        self._err_text.show()
        self._log.setPlainText(msg)
        self._result.show()
        if self._log.isHidden():
            self._toggle_log()
        self._set_status("")

    @Slot()
    def _cleanup_thread(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
        if self._thread is not None:
            self._thread.deleteLater()
            self._thread = None
        self._set_busy(False)

    def _open_excel(self) -> None:
        if self._last_output_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._last_output_path))

    def _open_folder(self) -> None:
        p = Path(self._last_output_path)
        if p.is_file():
            subprocess.Popen(["explorer", "/select,", str(p)])
        elif p.parent.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(p.parent)))

    def _toggle_log(self) -> None:
        show = self._log.isHidden()
        self._log.setVisible(show)
        self._log_btn.setText(
            "Ayrıntılı listeyi gizle  ▾" if show else "Ayrıntılı listeyi göster  ▸"
        )
