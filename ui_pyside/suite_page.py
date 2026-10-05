"""
Gelir hazırlama — PySide6 sayfası.
İş akışı: `gelirhazirlama.run_gelir_export` (içinde `isle_fatura_dosyasi` + TCMB vb.).
Bağımsız pencere: `ui_pyside.main_window`; birleşik suite de bu sayfayı doğrudan kullanır.
"""

from __future__ import annotations

import io
import subprocess
import traceback
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from PySide6.QtCore import QObject, QSettings, Qt, QThread, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QIntValidator
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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
from gelirhazirlama import AY_ADI_SIRALI, _default_ay_yil, run_gelir_export
from ui.branding import make_pyside_logo_label
from ui_pyside.style import PAGE_QSS, badge_pixmap, repolish

_AY_MAP_UI = {i + 1: name for i, name in enumerate(AY_ADI_SIRALI)}
_STB_LISTE_LIMIT = 30


class _SignalStream(io.TextIOBase):
    """print çıktısını satır satır sinyale çevirir (worker thread → arayüz)."""

    def __init__(self, emit) -> None:
        super().__init__()
        self._emit = emit
        self._buf = ""

    def write(self, s: str) -> int:
        self._buf += s
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            self._emit(line)
        return len(s)

    def flush(self) -> None:
        if self._buf:
            self._emit(self._buf)
            self._buf = ""


class _GelirWorker(QObject):
    """Arka planda `run_gelir_export`; stdout satırları canlı iletilir."""

    log_line = Signal(str)
    finished_ok = Signal(str, str, str, object)  # path, warn, summary, stats
    finished_err = Signal(str)

    def __init__(
        self,
        excel_path: str,
        ay_adi: str,
        yil: str,
        output_folder: str,
        pdf_paths: Optional[List[str]],
        rename_pdfs: bool = True,
    ) -> None:
        super().__init__()
        self._excel_path = excel_path
        self._ay_adi = ay_adi
        self._yil = yil
        self._output_folder = output_folder
        self._pdf_paths = pdf_paths
        self._rename_pdfs = rename_pdfs

    @Slot()
    def run(self) -> None:
        stream = _SignalStream(self.log_line.emit)
        stats: dict = {}
        try:
            with redirect_stdout(stream):
                path, warn, summary = run_gelir_export(
                    self._excel_path,
                    self._ay_adi,
                    self._yil,
                    self._output_folder,
                    self._pdf_paths,
                    rename_pdfs=self._rename_pdfs,
                    stats=stats,
                )
            stream.flush()
            self.finished_ok.emit(path, warn or "", summary or "", stats)
        except Exception as exc:  # noqa: BLE001
            stream.flush()
            self.log_line.emit(traceback.format_exc())
            self.finished_err.emit(str(exc))


def _label(text: str = "", name: Optional[str] = None) -> QLabel:
    w = QLabel(text)
    if name:
        w.setObjectName(name)
    return w


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


class GelirPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("gelirRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(PAGE_QSS)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._settings = QSettings("Antsis", "GelirHazirlama")
        self._excel_path = ""
        self._pdf_paths: List[str] = []
        self._output_dir = ""
        self._last_output_path = ""
        self._tcmb_istek = 0

        self._thread: QThread | None = None
        self._worker: _GelirWorker | None = None

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
        body.addWidget(self._build_period_card())

        self._run_btn = QPushButton("Excel'i Oluştur")
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
        self._log.setMinimumHeight(200)
        self._log.hide()
        body.addWidget(self._log)

        body.addStretch(1)
        self._refresh_ready()

    # ---------- kurulum ----------

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
        titles.addWidget(_label("Gelir Hazırlama", "appTitle"))
        titles.addWidget(_label("Satış faturaları → gelir kalemleri çalışma dosyası", "appSub"))
        h.addLayout(titles)
        h.addStretch(1)
        h.addWidget(_label(f"v{__version__}", "version"), alignment=Qt.AlignmentFlag.AlignTop)
        return header

    def _grid(self) -> QGridLayout:
        g = QGridLayout()
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(10)
        g.setColumnMinimumWidth(0, 22)
        g.setColumnMinimumWidth(1, 108)
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

    def _build_inputs_card(self) -> _Card:
        card = _Card("1", "Girdi dosyaları")
        g = self._grid()

        excel_icon = QLabel()
        excel_icon.setPixmap(badge_pixmap("#217346", "X"))
        g.addWidget(excel_icon, 0, 0)
        g.addWidget(_label("Ham Excel", "fieldLabel"), 0, 1)
        self._excel_chip = self._chip()
        g.addWidget(self._excel_chip, 0, 2)
        self._excel_btn = self._file_btn(self._pick_excel)
        g.addWidget(self._excel_btn, 0, 3)

        pdf_icon = QLabel()
        pdf_icon.setPixmap(badge_pixmap("#dc2626", "P"))
        g.addWidget(pdf_icon, 1, 0)
        g.addWidget(_label("Fatura PDF'leri", "fieldLabel"), 1, 1)
        pdf_cell = QHBoxLayout()
        pdf_cell.setSpacing(6)
        self._pdf_chip = self._chip()
        pdf_cell.addWidget(self._pdf_chip, stretch=1)
        self._pdf_clear = QPushButton("Temizle")
        self._pdf_clear.setObjectName("linkMuted")
        self._pdf_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pdf_clear.clicked.connect(self._clear_pdfs)
        pdf_cell.addWidget(self._pdf_clear)
        g.addLayout(pdf_cell, 1, 2)
        self._pdf_btn = self._file_btn(self._pick_pdfs)
        g.addWidget(self._pdf_btn, 1, 3)

        card.body.addLayout(g)
        self._set_chip(self._excel_chip, "")
        self._set_chip(self._pdf_chip, "", empty_text="İsteğe bağlı — STB, istisna, iade, sipariş")
        self._pdf_clear.hide()
        return card

    def _build_period_card(self) -> _Card:
        card = _Card("2", "Dönem ve çıktı")
        g = self._grid()

        g.addWidget(_label("Dönem", "fieldLabel"), 0, 1)
        period = QHBoxLayout()
        period.setSpacing(8)
        varsayilan_ay, varsayilan_yil = _default_ay_yil()
        self._ay_combo = QComboBox()
        self._ay_combo.addItems(list(AY_ADI_SIRALI))
        self._ay_combo.setMinimumWidth(150)
        idx = self._ay_combo.findText(varsayilan_ay)
        self._ay_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._yil_edit = QLineEdit(varsayilan_yil)
        self._yil_edit.setFixedWidth(80)
        self._yil_edit.setValidator(QIntValidator(2000, 2100, self))
        self._yil_edit.textChanged.connect(self._refresh_ready)
        period.addWidget(self._ay_combo)
        period.addWidget(self._yil_edit)
        period.addStretch(1)
        g.addLayout(period, 0, 2, 1, 2)

        g.addWidget(_label("Çıktı klasörü", "fieldLabel"), 1, 1)
        self._out_chip = self._chip()
        g.addWidget(self._out_chip, 1, 2)
        self._out_btn = self._file_btn(self._pick_output)
        g.addWidget(self._out_btn, 1, 3)

        card.body.addLayout(g)
        self._set_chip(self._out_chip, "")
        return card

    def _build_result_card(self) -> _Card:
        card = _Card("✓", "Sonuç")

        self._tiles_row = QWidget()
        tiles = QHBoxLayout(self._tiles_row)
        tiles.setContentsMargins(0, 0, 0, 0)
        tiles.setSpacing(10)
        self._tile_fatura = _Tile("fatura satırı")
        self._tile_stb = _Tile("STB kodu eksik")
        self._tile_kur = _Tile("kur boş satır")
        self._tile_pdf = _Tile("PDF seçildi")
        for t in (self._tile_fatura, self._tile_stb, self._tile_kur, self._tile_pdf):
            tiles.addWidget(t)
        card.body.addWidget(self._tiles_row)

        self._note = _label("", "note")
        self._note.setWordWrap(True)
        card.body.addWidget(self._note)

        self._err_text = _label("", "errText")
        self._err_text.setWordWrap(True)
        self._err_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        card.body.addWidget(self._err_text)

        self._stb_box = QWidget()
        stb_v = QVBoxLayout(self._stb_box)
        stb_v.setContentsMargins(0, 0, 0, 0)
        stb_v.setSpacing(4)
        stb_v.addWidget(_label("STB kodu eksik (iade olmayan) — Excel'de sarı işaretli", "warnHead"))
        self._stb_scroll = QScrollArea()
        self._stb_scroll.setWidgetResizable(True)
        self._stb_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._stb_scroll.setObjectName("stbScroll")
        self._stb_list_host = QWidget()
        self._stb_list_host.setObjectName("stbHost")
        self._stb_list = QVBoxLayout(self._stb_list_host)
        self._stb_list.setContentsMargins(0, 0, 0, 0)
        self._stb_list.setSpacing(4)
        self._stb_scroll.setWidget(self._stb_list_host)
        stb_v.addWidget(self._stb_scroll)
        card.body.addWidget(self._stb_box)

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
        self._log_btn = QPushButton("İşlem günlüğünü göster  ▸")
        self._log_btn.setObjectName("link")
        self._log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._log_btn.clicked.connect(self._toggle_log)
        actions.addWidget(self._open_excel_btn)
        actions.addWidget(self._open_dir_btn)
        actions.addStretch(1)
        actions.addWidget(self._log_btn)
        card.body.addLayout(actions)
        return card

    # ---------- yardımcılar ----------

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

    def _start_dir(self, key: str) -> str:
        d = self._settings.value(key, "", type=str)
        return d if d and Path(d).is_dir() else ""

    def _remember_dir(self, key: str, path: str) -> None:
        p = Path(path)
        self._settings.setValue(key, str(p if p.is_dir() else p.parent))

    def _set_status(self, text: str) -> None:
        self._status.setText(text)
        self._status.setVisible(bool(text))

    def _append_log(self, text: str) -> None:
        self._log.appendPlainText(text.rstrip("\n"))

    def _refresh_ready(self) -> None:
        busy = self._thread is not None and self._thread.isRunning()
        yil = self._yil_edit.text().strip() if hasattr(self, "_yil_edit") else ""
        ready = bool(self._excel_path and self._output_dir and len(yil) == 4)
        self._run_btn.setEnabled(ready and not busy)
        if busy:
            return
        if not self._excel_path:
            self._set_status("Başlamak için ham Excel dosyasını seçin.")
        elif not self._output_dir:
            self._set_status("Çıktının kaydedileceği klasörü seçin.")
        elif len(yil) != 4:
            self._set_status("Yılı dört haneli girin (ör. 2026).")
        else:
            self._set_status("")

    def _set_busy(self, busy: bool) -> None:
        for w in (self._excel_btn, self._pdf_btn, self._pdf_clear, self._out_btn, self._ay_combo, self._yil_edit):
            w.setEnabled(not busy)
        self._progress.setVisible(busy)
        self._run_btn.setText("İşleniyor…" if busy else "Excel'i Oluştur")
        self._refresh_ready()

    # ---------- seçimler ----------

    def _pick_excel(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Ham satış Excel'ini seçin",
            self._start_dir("dir/excel"),
            "Excel (*.xlsx *.xls);;Tüm dosyalar (*.*)",
        )
        if not path:
            return
        self._excel_path = path
        self._remember_dir("dir/excel", path)
        self._set_chip(self._excel_chip, Path(path).name, tooltip=path)
        self._excel_btn.setText("Değiştir")
        self._append_log(f"Excel seçildi: {path}")
        self._hint_ay_yil_from_excel(path)
        self._refresh_ready()

    def _hint_ay_yil_from_excel(self, file_path: str) -> None:
        try:
            df = pd.read_excel(file_path)
            if len(df) == 0 or len(df.columns) == 0:
                return
            first_date = df.iloc[0, 0]
            if pd.isna(first_date):
                return
            tarih: datetime | None = None
            if isinstance(first_date, datetime):
                tarih = first_date
            elif isinstance(first_date, str):
                try:
                    tarih = datetime.strptime(first_date.strip(), "%d.%m.%Y")
                except ValueError:
                    try:
                        tarih = pd.to_datetime(first_date, dayfirst=True).to_pydatetime()
                    except Exception:  # noqa: BLE001
                        tarih = None
            else:
                try:
                    tarih = pd.to_datetime(first_date).to_pydatetime()
                except Exception:  # noqa: BLE001
                    tarih = None
            if tarih:
                ay_adi = _AY_MAP_UI.get(tarih.month, _default_ay_yil()[0])
                idx = self._ay_combo.findText(ay_adi)
                if idx >= 0:
                    self._ay_combo.setCurrentIndex(idx)
                self._yil_edit.setText(str(tarih.year))
                self._append_log(f"Dönem Excel'in ilk tarihinden önerildi: {ay_adi} {tarih.year}")
        except Exception as exc:  # noqa: BLE001
            self._append_log(f"Dönem otomatik okunamadı: {exc}")

    def _pick_pdfs(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Fatura PDF'lerini seçin (çoklu)",
            self._start_dir("dir/pdf"),
            "PDF (*.pdf);;Tüm dosyalar (*.*)",
        )
        if not paths:
            return
        self._pdf_paths = list(paths)
        self._remember_dir("dir/pdf", paths[0])
        names = [Path(p).name for p in paths]
        tip = "\n".join(names[:25]) + (f"\n… ve {len(names) - 25} dosya daha" if len(names) > 25 else "")
        text = names[0] if len(names) == 1 else f"{len(names)} PDF seçildi"
        self._set_chip(self._pdf_chip, text, tooltip=tip)
        self._pdf_btn.setText("Değiştir")
        self._pdf_clear.show()
        self._append_log(f"{len(paths)} PDF seçildi.")

    def _clear_pdfs(self) -> None:
        self._pdf_paths = []
        self._set_chip(self._pdf_chip, "", empty_text="İsteğe bağlı — STB, istisna, iade, sipariş")
        self._pdf_btn.setText("Seç…")
        self._pdf_clear.hide()

    def _pick_output(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Çıktı klasörünü seçin", self._start_dir("dir/output"))
        if not d:
            return
        self._output_dir = d
        self._remember_dir("dir/output", d)
        self._set_chip(self._out_chip, d, tooltip=d)
        self._out_btn.setText("Değiştir")
        self._append_log(f"Çıktı klasörü: {d}")
        self._refresh_ready()

    # ---------- işlem ----------

    def _on_run(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            return
        excel = Path(self._excel_path)
        if not excel.is_file():
            QMessageBox.warning(self, "Gelir hazırlama", f"Excel dosyası bulunamadı:\n{excel}")
            return
        if not Path(self._output_dir).is_dir():
            QMessageBox.warning(self, "Gelir hazırlama", f"Çıktı klasörü bulunamadı:\n{self._output_dir}")
            return
        ay_adi = self._ay_combo.currentText().strip()
        yil = self._yil_edit.text().strip()

        rename_pdfs = True
        pdfs = self._pdf_paths or None
        if pdfs:
            reply = QMessageBox.question(
                self,
                "PDF yeniden adlandırma",
                f"{len(pdfs)} PDF seçildi.\n\n"
                "Eşleşen PDF dosyaları kaynak klasörde yeniden adlandırılsın mı?\n\n"
                "Hayır derseniz Excel yine üretilir; PDF içinden STB/istisna/iade "
                "eşlemesi yapılır, dosya adları değişmez.",
            )
            rename_pdfs = reply == QMessageBox.StandardButton.Yes

        self._result.hide()
        self._tcmb_istek = 0
        self._append_log(f"--- İşlem başladı: {ay_adi} {yil} ---")
        self._set_status("Excel okunuyor…")

        self._thread = QThread(self)
        self._worker = _GelirWorker(self._excel_path, ay_adi, yil, self._output_dir, pdfs, rename_pdfs=rename_pdfs)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log_line.connect(self._on_log_line)
        self._worker.finished_ok.connect(self._on_ok)
        self._worker.finished_err.connect(self._on_err)
        self._worker.finished_ok.connect(self._thread.quit)
        self._worker.finished_err.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)
        self._thread.start()
        self._set_busy(True)

    @Slot(str)
    def _on_log_line(self, line: str) -> None:
        self._append_log(line)
        if "[TCMB] URL denenecek" in line:
            self._tcmb_istek += 1
            self._set_status(f"TCMB kurları alınıyor… ({self._tcmb_istek} istek)")
        elif "[TCMB]" in line:
            pass
        elif "PDF" in line and self._tcmb_istek == 0:
            self._set_status("PDF'ler okunuyor…")

    @Slot(str, str, str, object)
    def _on_ok(self, path: str, warn: str, summary: str, stats: object) -> None:
        stats = stats if isinstance(stats, dict) else {}
        self._last_output_path = path
        if summary.strip():
            self._append_log("--- Özet ---\n" + summary)
        self._append_log("--- İşlem bitti ---")

        self._result.set_head("✓", "Sonuç", tone="ok")
        self._tiles_row.show()
        self._err_text.hide()
        self._open_excel_btn.show()
        self._open_dir_btn.show()

        self._tile_fatura.set_value(str(stats.get("fatura_satiri", "—")))
        stb_eksik = stats.get("stb_eksik", [])
        if stats.get("stb_kontrol_yapildi"):
            self._tile_stb.set_value(str(len(stb_eksik)), "STB kodu eksik", warn=bool(stb_eksik))
        else:
            self._tile_stb.set_value("—", "STB kontrolü yok (PDF seçilmedi)", warn=True)
        kur_bos = int(stats.get("kur_bos", 0) or 0)
        self._tile_kur.set_value(str(kur_bos), "kur boş satır", warn=kur_bos > 0)
        self._tile_pdf.set_value(str(stats.get("pdf_secilen", 0)), "PDF seçildi")

        self._fill_stb_list(stb_eksik)
        self._note.setText(warn)
        self._note.setVisible(bool(warn))
        self._path_label.setText(f"Kaydedildi: {Path(path).name}")
        self._path_label.setToolTip(path)
        self._result.show()
        self._set_status("")

    def _fill_stb_list(self, rows) -> None:
        while self._stb_list.count():
            item = self._stb_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not rows:
            self._stb_box.hide()
            return
        for fno, firma, sebep in rows[:_STB_LISTE_LIMIT]:
            lbl = _label(f"•  {fno}  {firma} — {sebep}", "warnRow")
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._stb_list.addWidget(lbl)
        if len(rows) > _STB_LISTE_LIMIT:
            self._stb_list.addWidget(_label(f"… ve {len(rows) - _STB_LISTE_LIMIT} fatura daha (günlükte tam liste)", "warnRow"))
        shown = min(len(rows), _STB_LISTE_LIMIT) + (1 if len(rows) > _STB_LISTE_LIMIT else 0)
        self._stb_scroll.setFixedHeight(min(shown, 8) * 22 + 4)
        self._stb_box.show()

    @Slot(str)
    def _on_err(self, msg: str) -> None:
        self._append_log("--- İşlem hata ile bitti ---")
        self._result.set_head("!", "İşlem tamamlanamadı", tone="err")
        self._tiles_row.hide()
        self._stb_box.hide()
        self._note.hide()
        self._open_excel_btn.hide()
        self._open_dir_btn.hide()
        self._path_label.setText("")
        self._err_text.setText(msg or "Bilinmeyen hata.")
        self._err_text.show()
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

    # ---------- sonuç eylemleri ----------

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
        self._log_btn.setText("İşlem günlüğünü gizle  ▾" if show else "İşlem günlüğünü göster  ▸")
