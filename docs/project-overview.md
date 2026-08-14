# Gelir Hazırlama - Project Overview

**Date:** 2026-07-12  
**Type:** Desktop (Python)  
**Architecture:** File-based ETL pipeline with dual UI shells

## Executive Summary

**Gelir Hazırlama**, satış faturalarının ham Excel listesini muhasebe/teknopark süreçlerinde kullanılan standart **gelir kalemleri çalışma** dosyasına dönüştürür. PDF’lerden Teknopark (STB) kodu, istisna/iade metinleri ve sipariş bilgileri alınabilir; USD dönüşümleri için TCMB ForexBuying kullanılır.

## Project Classification

- **Repository Type:** Monolith
- **Project Type(s):** desktop
- **Primary Language(s):** Python
- **Architecture Pattern:** Single processing core + presentation adapters (Tkinter native, PySide6 suite page)

## Technology Stack Summary

| Category | Technology | Version / Not | Justification |
|----------|------------|---------------|---------------|
| Language | Python | 3.12+ | Ana uygulama |
| Data | pandas | ≥1.5 | Excel okuma/işleme |
| Excel write | openpyxl | ≥3.0 | SUM formül, stil, U/V |
| Numeric | numpy | ≥1.20 | mask / nan |
| PDF | pdfplumber | ≥0.10 | Fatura metin çıkarımı (opsiyonel) |
| UI (standalone) | Tkinter | stdlib | Varsayılan arayüz |
| UI (suite) | PySide6 | ayrı kurulum | Birleşik kabuk sayfası |
| Network | urllib + ssl | stdlib | TCMB XML |
| Packaging | PyInstaller | ≥5.0 | Tek dosya EXE |

## Key Features

- Ham satış Excel → gelir kalemleri çalışma Excel
- Otomatik ay/yıl önerisi (ilk satır tarihi)
- Çoklu PDF: STB, KDV istisna, iade, sipariş, AWSOLS not
- TCMB kur + Kur MB referans sütunu
- PDF dosya yeniden adlandırma (`FATURA_FIRMA.pdf`)
- Açık dosya durumunda zaman damgalı yedek çıktı

## Architecture Highlights

- **Tek kaynak doğruluk:** `run_gelir_export` hem Tk hem PySide tarafından çağrılır.
- **Kolon eşlemesi indeks tabanlı** — şablon kırılganlığı bilinçli kabul.
- **Ağ bağımlılığı** yalnızca TCMB; başarısızlıkta ilgili satırda kur boş / uyarı log.

## Development Overview

### Prerequisites

Python, venv, `requirements.txt` paketleri; PDF için pdfplumber; suite için PySide6.

### Getting Started

`run_app.bat` veya `python gelirhazirlama.py`.

### Key Commands

- **Install:** `pip install -r requirements.txt`
- **Dev:** `python gelirhazirlama.py`
- **Build:** `build_exe.bat`
- **Test:** Otomatik test suite yok (manuel Excel/PDF doğrulama)

## Repository Structure

Tek kök: iş motoru + Tk (`gelirhazirlama.py`), opsiyonel PySide paketi (`ui_pyside/`), build betikleri.

## Documentation Map

- [NOT_DEFTERI.md](./NOT_DEFTERI.md) — hatırlatma notu
- [index.md](./index.md) — master index
- [architecture.md](./architecture.md)
- [source-tree-analysis.md](./source-tree-analysis.md)
- [development-guide.md](./development-guide.md)

---

_Generated using BMAD Method `document-project` workflow_
