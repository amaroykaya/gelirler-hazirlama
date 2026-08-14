# Gelir Hazırlama — Development Guide

**Date:** 2026-07-12

## Prerequisites

- Windows
- Python 3.12+ (PATH’te `py` / `python` veya yaygın kurulum yolları)
- Git (opsiyonel)
- İnternet (TCMB kur testleri için)

## Environment setup

```powershell
cd "c:\Users\Asus.DESKTOP-9F6EQVL\Desktop\tools\gelir_hazırlama"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Suite PySide sayfasını kullanacaksan:

```powershell
pip install PySide6
```

## Run

```powershell
# Önerilen
.\run_app.bat

# veya
python gelirhazirlama.py
```

`run_app.bat` `.venv\Scripts\activate.bat` yoksa hata verip çıkar.

## Build

```powershell
.\build_exe.bat
```

Betik: bağımlılıkları pip ile kurar → PyInstaller `--onefile --windowed --name=GelirHazirlama` → `dist\GelirHazirlama.exe`.

Alternatif: `pyinstaller GelirHazirlama.spec`

## Common tasks

| Görev | Nerede |
|-------|--------|
| Yeni Excel kolonu | `isle_fatura_dosyasi` iloc eşlemeleri + `column_order` |
| Yeni PDF alanı | Yeni `extract_*` + map + eşleme döngüsü |
| Kur kuralı | `get_tcmb_dollar_rate` / Kur & Kur MB blokları |
| Tk alan ekle | `GelirHazirlamaApp.__init__` + `process_file` |
| Suite alan ekle | `GelirPage` + `_GelirWorker` args |

## Testing approach

Otomatik test yok. Manuel checklist:

1. Normal USD fatura — Kur / Kur MB dolu mu?
2. TL fatura — TCMB ile USD hesaplandı mı?
3. EURO döviz — EURO kolonu Q değerini aldı mı?
4. İADE — USD 0, Özel Açıklama?
5. KDV 0 + PDF — istisna metni?
6. AWSOLS + PDF not — Açıklama’ya `- ` satırlar?
7. Çok satırlı fatura — açıklamalar birleşti mi?
8. PDF rename + AMBIGUOUS senaryosu
9. Çıktı dosyası açıkken → timestamp’li dosya

## Code conventions (gözlenen)

- Türkçe UI metinleri ve çoğu print log
- İş mantığı print ile izlenir (PySide stdout redirect)
- Tip ipuçları kısmi (`run_gelir_export`, suite)

## Related docs

- [NOT_DEFTERI.md](./NOT_DEFTERI.md)
- [architecture.md](./architecture.md)
- [deployment-guide.md](./deployment-guide.md)

---

_Generated using BMAD Method `document-project` workflow_
