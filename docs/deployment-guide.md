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
3. Sürüm `app_info.py` → `__version__`’dan okunur.
4. PyInstaller: `--onefile --windowed --name=GelirHazirlama-<sürüm> --hidden-import=pdfplumber --hidden-import=ui_pyside.main_window` + branding/ikon → `gelirhazirlama.py`
5. Çıktı: `dist\GelirHazirlama-<sürüm>.exe` (ör. `GelirHazirlama-1.4.0.exe`)

`GelirHazirlama.spec`: `console=False`, `upx=True`, aynı giriş noktası.

## What is packaged

- `gelirhazirlama.py` ve bağımlılıkları (pandas, openpyxl, numpy, pdfplumber, PySide6, …)
- `ui_pyside` (PySide6 arayüz — EXE açılışta bunu gösterir), `ui/branding.py`, `assets/branding`
- Tk arayüzü yedek olarak içeride kalır (`--tk`)
- EXE boyutu PySide6 nedeniyle ~70–90 MB

## Distribution

- `GelirHazirlama-<sürüm>.exe` dosyasını kullanıcıya ver.
- İlk çalıştırmada Windows SmartScreen uyarısı çıkabilir (imzasız build).
- Kullanıcıya: Excel formatının kolon sırasının değişmemesi gerektiğini hatırlat.

## Environment configuration

`.env` veya remote config yok. Ay/yıl UI’dan; kur TCMB’den canlı çekilir.

## CI/CD

Repoda GitHub Actions / benzeri pipeline yok. Build yerel bat ile.

## Rollback

Önceki sürümün `dist\GelirHazirlama-<eski sürüm>.exe` dosyasını kullan (her sürüm ayrı adla üretilir). Kaynak için git geçmişi.

---

_Generated using BMAD Method `document-project` workflow_
