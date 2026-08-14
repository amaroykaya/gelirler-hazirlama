# Gelir Hazırlama - Source Tree Analysis

**Date:** 2026-07-12

## Overview

Küçük monolith masaüstü proje. Kaynak kod birkaç dosyada; `dist/` / `build/` / `.venv` üretim ve ortam klasörleridir.

## Complete Directory Structure

```
gelir_hazırlama/
├── gelirhazirlama.py      # İş motoru + Tk UI + giriş noktası ★
├── ui_pyside/             # Suite için PySide6 sayfası
│   ├── __init__.py
│   └── suite_page.py      # GelirPage, _GelirWorker
├── docs/                  # BMAD proje bilgisi + not defteri
│   ├── NOT_DEFTERI.md     # İnsan odaklı hatırlatma ★
│   ├── index.md
│   ├── architecture.md
│   └── …
├── run_app.bat            # .venv + python gelirhazirlama.py
├── build_exe.bat          # pip + PyInstaller onefile
├── GelirHazirlama.spec    # PyInstaller spec
├── requirements.txt
├── .gitignore
├── assets/                # gitignore; yerel varlıklar
├── dist/                  # EXE çıktısı (gitignore)
├── build/                 # PyInstaller ara (gitignore)
└── .venv/                 # Sanal ortam (gitignore)
```

## Critical Directories

### `./` (kök)

**Purpose:** Ana uygulama ve build girişleri.  
**Contains:** `gelirhazirlama.py`, bat dosyaları, requirements.  
**Entry Points:** `gelirhazirlama.py` → `__main__`

### `ui_pyside/`

**Purpose:** Birleşik araç kabuğuna gömülen PySide sayfası.  
**Contains:** `GelirPage` formu, QThread worker.  
**Integration:** `from gelirhazirlama import run_gelir_export`

### `docs/`

**Purpose:** Proje bilgisi ve AI/insan bağlamı.  
**Contains:** NOT_DEFTERI, architecture, guides.

## Entry Points

- **Main Entry:** `gelirhazirlama.py` — `GelirHazirlamaApp` + `root.mainloop()`
- **Library API:** `run_gelir_export(...)` — UI-agnostik export
- **Suite Entry:** `ui_pyside.suite_page.GelirPage` (harici host)

## File Organization Patterns

- İş kuralları ve Tk UI aynı dosyada (tarihsel monolith).
- PySide ince adapter; iş mantığı kopyalanmaz.
- Kalıcı config / DB yok; tüm durum oturum + seçilen dosya yolları.

## Key File Types

### Python

- **Pattern:** `*.py`
- **Purpose:** Uygulama ve UI
- **Examples:** `gelirhazirlama.py`, `suite_page.py`

### Batch / Spec

- **Pattern:** `*.bat`, `*.spec`
- **Purpose:** Çalıştırma ve paketleme
- **Examples:** `run_app.bat`, `GelirHazirlama.spec`

## Asset Locations

`assets/` `.gitignore`’da; repoda içerik beklenmez.

## Configuration Files

- **`requirements.txt`:** Runtime + PyInstaller bağımlılıkları (PySide6 yok)
- **`GelirHazirlama.spec`:** Analysis/EXE ayarları (`console=False`)
- **`.gitignore`:** venv, dist, build, assets, yerel gürültü

## Notes for Development

EXE üretimi yalnızca `gelirhazirlama.py` paketler; `ui_pyside` suite senaryosu ayrı host’a bağlıdır.

---

_Generated using BMAD Method `document-project` workflow_
