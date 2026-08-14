# Gelir Hazırlama — Deployment Guide

**Date:** 2026-07-12

## Target

Windows masaüstü kullanıcıları; kurulum gerektirmeyen tek EXE veya kaynak + venv.

## Infrastructure requirements

- Windows 10/11
- İnternet (TCMB XML; offline’da kur alanları boş kalabilir)
- Yazma izni: çıktı klasörü + (PDF rename için) PDF’lerin bulunduğu klasör

## Build process

1. `build_exe.bat` çalıştır.
2. Python bulunur, paketler kurulur.
3. PyInstaller: `--onefile --windowed --name=GelirHazirlama --hidden-import=pdfplumber gelirhazirlama.py`
4. Çıktı: `dist\GelirHazirlama.exe`

`GelirHazirlama.spec`: `console=False`, `upx=True`, aynı giriş noktası.

## What is packaged

- `gelirhazirlama.py` ve bağımlılıkları (pandas, openpyxl, numpy, pdfplumber, …)
- **Paketlenmez:** `ui_pyside` / PySide6 suite

## Distribution

- `GelirHazirlama.exe` dosyasını kullanıcıya ver.
- İlk çalıştırmada Windows SmartScreen uyarısı çıkabilir (imzasız build).
- Kullanıcıya: Excel formatının kolon sırasının değişmemesi gerektiğini hatırlat.

## Environment configuration

`.env` veya remote config yok. Ay/yıl UI’dan; kur TCMB’den canlı çekilir.

## CI/CD

Repoda GitHub Actions / benzeri pipeline yok. Build yerel bat ile.

## Rollback

Önceki `dist\GelirHazirlama.exe` yedeğini geri koy. Kaynak için git geçmişi.

---

_Generated using BMAD Method `document-project` workflow_
