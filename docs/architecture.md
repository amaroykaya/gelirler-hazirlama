# Gelir Hazırlama — Architecture

**Date:** 2026-07-12  
**Pattern:** Desktop ETL · single core · dual presentation

## Executive Summary

Uygulama dosya tabanlı bir dönüşüm boru hattıdır. Ham Excel + opsiyonel PDF → zenginleştirilmiş DataFrame → openpyxl ile formüllü çalışma kitabı. Sunucu/DB yoktur.

## Technology Stack

Bkz. [project-overview.md](./project-overview.md). Ağ: yalnızca TCMB `kurlar/{YYYYMM}/{ddMMyyyy}.xml`, USD `ForexBuying`.

## Architecture Pattern

```
[Tk GelirHazirlamaApp] ──┐
                          ├──► run_gelir_export ──► isle_fatura_dosyasi ──► DataFrame
[PySide GelirPage/QThread]┘                              │
                                                         ├── PDF extract_* maps
                                                         ├── TCMB get_tcmb_dollar_rate
                                                         └── kurallar / sıralama
                                                              │
                                                              ▼
                                              _save_gelir_workbook_formulas
                                                              │
                                                              ▼
                                              gelir_kalemleri_{ay}_{yil}_çalışma.xlsx
```

## Data Architecture

### Girdi

- Excel: `pd.read_excel`; sütunlar **iloc indeksi** (NOT_DEFTERI’deki tablo).
- PDF: `pdfplumber` metin + regex extractor’lar; anahtar = fatura no (uppercase).

### İşlenmiş model (`final_tot`)

Çıktı kolon sırası ve sipariş alanları için [NOT_DEFTERI.md](./NOT_DEFTERI.md) §5–6.

### Kalıcılık

Yalnızca kullanıcı seçtiği çıktı klasörüne yazılan `.xlsx`. PDF rename kaynak dizinde yan etki.

## API Design

Harici HTTP API yok. Dahili public yüzey:

```python
run_gelir_export(
    excel_path: str,
    ay_adi_excel: str,   # "EYLÜL" …
    yil: str,
    output_folder: str,
    pdf_paths: Optional[List[str]] = None,
) -> Tuple[str, Optional[str]]  # (path, warn)
```

## Component Overview

| Katman | Bileşen | Not |
|--------|---------|-----|
| Presentation | `GelirHazirlamaApp` | Tk, senkron işlem |
| Presentation | `GelirPage` | PySide, QThread |
| Application | `run_gelir_export` | Orkestrasyon + PermissionError yedek |
| Domain | `isle_fatura_dosyasi` | Tüm iş kuralları |
| Domain | `extract_*` | PDF alanları |
| Infrastructure | `_fetch_tcmb_xml` / `get_tcmb_dollar_rate` | Kur |
| Infrastructure | `_save_gelir_workbook_formulas` | Excel son işlem |

## Business Rules (özet)

Detay: [NOT_DEFTERI.md](./NOT_DEFTERI.md) §7.

1. Tarih dolu satır = fatura başlığı; boş tarih satırları gruba bağlanır, çıktıda düşer.
2. Firma: D → yoksa (E doluysa) C.
3. Açıklama birleştirme; INSURANCE/FREIGHT blocklist.
4. PDF içerik eşlemesi birebir fatura no; rename’de rakam fallback + ambiguity.
5. İADE → USD=0 + Özel Açıklama.
6. KDV0 → istisna metni Özel Açıklama.
7. AWSOLS → PDF not → Açıklama.
8. Non-USD/TRL/TRY → EURO = Q.
9. TL≈USD → USD sıfır; sonra TCMB yolları devreye girebilir.
10. Kur vs Kur MB ayrımı.
11. Fatura no sıralama + No renumber.

## Source Tree

[source-tree-analysis.md](./source-tree-analysis.md)

## Development Workflow

[development-guide.md](./development-guide.md)

## Deployment Architecture

Standalone Windows EXE (Tk). Suite senaryosu ayrı host + `ui_pyside`.  
[deployment-guide.md](./deployment-guide.md)

## Testing Strategy

Otomatik test yok. Manuel: örnek ham Excel + PDF seti, TCMB erişimi açık/kapalı, iade/KDV0/AWSOLS/EURO senaryoları, dosya açıkken PermissionError yedek adı.

## Non-goals / Constraints

- Ham Excel şeması sabit indeks varsayımı.
- EXE `ui_pyside` içermez.
- `requests` bağımlılığı fiilen kullanılmıyor (urllib).

---

_Generated using BMAD Method `document-project` workflow_
