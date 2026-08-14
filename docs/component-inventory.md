# Gelir Hazırlama — Component Inventory

**Date:** 2026-07-12

## Processing / Domain

| Component | Location | Type | Responsibility |
|-----------|----------|------|----------------|
| `_fetch_tcmb_xml` | `gelirhazirlama.py` | Function | TCMB XML indir (SSL default→fallback, 3 deneme) |
| `get_tcmb_dollar_rate` | `gelirhazirlama.py` | Function | Önceki iş günü USD ForexBuying |
| `extract_fatura_no_from_filename` | `gelirhazirlama.py` | Function | PDF adından fatura no |
| `extract_stb_proje_kodu` | `gelirhazirlama.py` | Function | STB proje kodu |
| `extract_vergi_istisna_muafiyet_sebebi` | `gelirhazirlama.py` | Function | İstisna/muafiyet metni |
| `extract_iade_aciklama` | `gelirhazirlama.py` | Function | İade açıklaması |
| `extract_not_fatura_aciklama` | `gelirhazirlama.py` | Function | Not: Fatura Açıklaması |
| `extract_siparis_bilgileri` | `gelirhazirlama.py` | Function | Sipariş No + Sorumlu |
| `isle_fatura_dosyasi` | `gelirhazirlama.py` | Function | Ana dönüşüm pipeline |
| `_coerce_numeric_columns` | `gelirhazirlama.py` | Function | Güvenli numeric coerce + log |
| `_save_gelir_workbook_formulas` | `gelirhazirlama.py` | Function | Excel yaz, SUM, kırmızı, U/V |
| `run_gelir_export` | `gelirhazirlama.py` | Function | Ortak export API |
| `AY_ADI_DOSYA_MAP` | `gelirhazirlama.py` | Constant | Excel ay → dosya adı ASCII |

## UI — Tkinter

| Component | Location | Category | Notes |
|-----------|----------|----------|-------|
| `GelirHazirlamaApp` | `gelirhazirlama.py` | Form / Window | Excel, PDF, ay, yıl, çıktı, İşle |
| `select_file` | method | Navigation | Ay/yıl auto-hint |
| `select_pdf_files` | method | Form | Çoklu PDF |
| `select_output_folder` | method | Form | Klasör |
| `process_file` | method | Action | `run_gelir_export` senkron |

## UI — PySide6

| Component | Location | Category | Notes |
|-----------|----------|----------|-------|
| `GelirPage` | `ui_pyside/suite_page.py` | Page / Form | Suite gömülü sayfa |
| `_GelirWorker` | `ui_pyside/suite_page.py` | Worker | QThread + stdout capture |
| `_AYLAR` / `_AY_MAP_UI` | `suite_page.py` | Constants | Ay listesi / map |

## Layout / Display widgets (PySide)

- `QGroupBox` “Girdi / çıktı”
- `QFormLayout`: Excel, PDF, Ay, Yıl, Çıktı
- `QPushButton` “İşle”
- `QLabel` durum
- `QPlainTextEdit` işlem günlüğü

## Reusable vs specific

- **Reusable:** `run_gelir_export` ve tüm `extract_*` / TCMB / `isle_fatura_dosyasi`
- **Specific:** Her UI kendi dosya seçici ve durum gösterimi

## Design system

Yok; platform varsayılan widget stilleri.

---

_Generated using BMAD Method `document-project` workflow_
