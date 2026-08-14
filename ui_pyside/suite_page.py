"""
Gelir hazırlama — PySide6 sayfası.
İş akışı: `gelirhazirlama.run_gelir_export` (içinde `isle_fatura_dosyasi` + TCMB vb.).
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from gelirhazirlama import AY_ADI_SIRALI, _default_ay_yil, run_gelir_export

_AYLAR = AY_ADI_SIRALI

_AY_MAP_UI = {i + 1: name for i, name in enumerate(AY_ADI_SIRALI)}


class _GelirWorker(QObject):
    """Arka planda `run_gelir_export`; stdout yakalanır (print tabanlı izleme)."""

    finished_ok = Signal(str, str, str, str)  # path, warn, summary, log_tail
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
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                path, warn, summary = run_gelir_export(
                    self._excel_path,
                    self._ay_adi,
                    self._yil,
                    self._output_folder,
                    self._pdf_paths,
                    rename_pdfs=self._rename_pdfs,
                )
            raw = buf.getvalue()
            tail = raw[-12000:] if len(raw) > 12000 else raw
            self.finished_ok.emit(path, warn or "", summary or "", tail)
        except Exception as exc:  # noqa: BLE001
            raw = buf.getvalue()
            tail = raw[-6000:] if len(raw) > 6000 else raw
            self.finished_err.emit(f"{exc}\n\n--- stdout ---\n{tail}")


class GelirPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self._excel_path = ""
        self._pdf_paths: List[str] = []
        self._output_dir = ""

        self._thread: QThread | None = None
        self._worker: _GelirWorker | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        paths = QGroupBox("Girdi / çıktı")
        form = QFormLayout(paths)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._excel_edit = QLineEdit()
        self._excel_edit.setReadOnly(True)
        self._excel_edit.setPlaceholderText("Henüz seçilmedi")
        form.addRow("Excel:", self._file_row(self._excel_edit, self._pick_excel))

        self._pdf_edit = QLineEdit()
        self._pdf_edit.setReadOnly(True)
        self._pdf_edit.setPlaceholderText("İsteğe bağlı — çoklu PDF")
        form.addRow("PDF (STB vb.):", self._file_row(self._pdf_edit, self._pick_pdfs))

        _varsayilan_ay, _varsayilan_yil = _default_ay_yil()
        self._ay_combo = QComboBox()
        self._ay_combo.addItems(list(_AYLAR))
        idx = self._ay_combo.findText(_varsayilan_ay)
        self._ay_combo.setCurrentIndex(idx if idx >= 0 else 0)
        form.addRow("Ay:", self._ay_combo)

        self._yil_edit = QLineEdit(_varsayilan_yil)
        form.addRow("Yıl:", self._yil_edit)

        self._out_edit = QLineEdit()
        self._out_edit.setReadOnly(True)
        self._out_edit.setPlaceholderText("Henüz seçilmedi")
        form.addRow("Çıktı klasörü:", self._file_row(self._out_edit, self._pick_output))

        root.addWidget(paths)

        self._run_btn = QPushButton("İşle")
        self._run_btn.clicked.connect(self._on_run)
        root.addWidget(self._run_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self._status = QLabel("Durum: Hazır")
        self._status.setWordWrap(True)
        root.addWidget(self._status)

        log_label = QLabel("İşlem günlüğü (stdout):")
        root.addWidget(log_label)
        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(180)
        self._log.setPlaceholderText("İşlem başlayınca burada çıktı görünür…")
        root.addWidget(self._log, stretch=1)

    def _file_row(self, edit: QLineEdit, slot) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        btn = QPushButton("Seç…")
        btn.clicked.connect(slot)
        h.addWidget(btn)
        h.addWidget(edit, stretch=1)
        return w

    def _pick_excel(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Excel Dosyası Seç",
            "",
            "Excel (*.xlsx *.xls);;Tüm dosyalar (*.*)",
        )
        if not path:
            return
        self._excel_path = path
        self._excel_edit.setText(path)
        self._append_log(f"Excel seçildi: {path}\n")
        self._hint_ay_yil_from_excel(path)

    def _hint_ay_yil_from_excel(self, file_path: str) -> None:
        try:
            df = pd.read_excel(file_path)
            if len(df) > 0 and len(df.columns) > 0:
                first_date = df.iloc[0, 0]
                if pd.notna(first_date):
                    tarih: datetime | None = None
                    if isinstance(first_date, datetime):
                        tarih = first_date
                    elif isinstance(first_date, str):
                        try:
                            tarih = datetime.strptime(first_date, "%d.%m.%Y")
                        except ValueError:
                            try:
                                tarih = pd.to_datetime(first_date).to_pydatetime()
                            except Exception:
                                tarih = None
                    else:
                        try:
                            tarih = pd.to_datetime(first_date).to_pydatetime()
                        except Exception:
                            tarih = None
                    if tarih:
                        ay_adi = _AY_MAP_UI.get(tarih.month, _default_ay_yil()[0])
                        idx = self._ay_combo.findText(ay_adi)
                        if idx >= 0:
                            self._ay_combo.setCurrentIndex(idx)
                        self._yil_edit.setText(str(tarih.year))
                        self._append_log(
                            f"Ay/yıl Excel ilk hücreden önerildi: {ay_adi} {tarih.year}\n"
                        )
        except Exception as exc:  # noqa: BLE001
            self._append_log(f"Otomatik ay/yıl okunamadı: {exc}\n")

    def _pick_pdfs(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "PDF Dosyaları (çoklu)",
            "",
            "PDF (*.pdf);;Tüm dosyalar (*.*)",
        )
        if not paths:
            return
        self._pdf_paths = list(paths)
        if len(paths) == 1:
            self._pdf_edit.setText(Path(paths[0]).name)
        else:
            self._pdf_edit.setText(f"{len(paths)} PDF seçildi")
        self._append_log(f"{len(paths)} PDF seçildi.\n")

    def _pick_output(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Çıktı Klasörü Seç")
        if not d:
            return
        self._output_dir = d
        self._out_edit.setText(d)
        self._append_log(f"Çıktı klasörü: {d}\n")

    def _append_log(self, text: str) -> None:
        self._log.appendPlainText(text.rstrip("\n"))

    def _on_run(self) -> None:
        if not self._excel_path:
            QMessageBox.warning(self, "Gelir hazırlama", "Lütfen bir Excel dosyası seçin.")
            return
        if not self._output_dir:
            QMessageBox.warning(self, "Gelir hazırlama", "Lütfen çıktı klasörünü seçin.")
            return
        ay_adi = self._ay_combo.currentText().strip()
        if not ay_adi:
            QMessageBox.warning(self, "Gelir hazırlama", "Lütfen ay seçin.")
            return
        yil = self._yil_edit.text().strip()
        if not yil:
            QMessageBox.warning(self, "Gelir hazırlama", "Lütfen yıl girin.")
            return

        if self._thread is not None and self._thread.isRunning():
            return

        rename_pdfs = True
        pdfs = self._pdf_paths if self._pdf_paths else None
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

        self._run_btn.setEnabled(False)
        self._status.setText("Durum: İşleniyor… (TCMB ağı kullanılıyor olabilir)")
        self._append_log("--- İşlem başladı ---\n")

        self._thread = QThread(self)
        self._worker = _GelirWorker(
            self._excel_path, ay_adi, yil, self._output_dir, pdfs, rename_pdfs=rename_pdfs
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished_ok.connect(self._on_ok)
        self._worker.finished_err.connect(self._on_err)
        self._worker.finished_ok.connect(self._thread.quit)
        self._worker.finished_err.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)
        self._thread.start()

    @Slot(str, str, str, str)
    def _on_ok(self, path: str, warn: str, summary: str, log_tail: str) -> None:
        self._run_btn.setEnabled(True)
        if log_tail.strip():
            self._append_log(log_tail)
        if summary.strip():
            self._append_log("--- Özet ---\n" + summary + "\n")
        self._append_log("--- İşlem bitti ---\n")
        self._status.setText(f"Durum: ✓ Tamamlandı — {path}")
        ozet = f"\n\n--- Özet ---\n{summary}" if summary.strip() else ""
        if warn:
            QMessageBox.warning(self, "Gelir hazırlama", f"{warn}\n\n{path}{ozet}")
        else:
            QMessageBox.information(self, "Gelir hazırlama", f"Dosya kaydedildi:\n{path}{ozet}")
        url = QUrl.fromLocalFile(path)
        if url.isValid():
            QDesktopServices.openUrl(url)

    @Slot(str)
    def _on_err(self, msg: str) -> None:
        self._run_btn.setEnabled(True)
        self._append_log(msg)
        self._append_log("--- İşlem hata ile bitti ---\n")
        self._status.setText("Durum: Hata — ayrıntı günlükte")
        QMessageBox.critical(self, "Gelir hazırlama", msg[:4000])

    @Slot()
    def _cleanup_thread(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
        if self._thread is not None:
            self._thread.deleteLater()
            self._thread = None
