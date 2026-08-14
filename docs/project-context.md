---
project_name: 'Gelir Hazırlama'
user_name: 'Asus'
date: '2026-07-12'
sections_completed:
  - technology_stack
  - language_rules
  - framework_rules
  - testing_rules
  - quality_rules
  - workflow_rules
  - anti_patterns
status: 'complete'
rule_count: 42
optimized_for_llm: true
existing_patterns_found: 18
---

# Project Context for AI Agents

_Bu dosya, bu projede kod yazarken AI agent’ların uyması gereken kritik kuralları içerir. Odak: agent’ların kaçırabileceği, bariz olmayan detaylar. İnsan hatırlatması için ayrıca `docs/NOT_DEFTERI.md` okunabilir._

---

## Technology Stack & Versions

| Paket / araç | Kısıt | Not |
|--------------|-------|-----|
| Python | 3.12+ (build 3.12–3.14 arar) | Ana dil |
| pandas | ≥1.5.0 | Excel + DataFrame |
| openpyxl | ≥3.0.0 | SUM, font, U/V kolonları |
| numpy | ≥1.20.0 | `nan`, maskeler |
| pdfplumber | ≥0.10.0 | Opsiyonel; yoksa PDF kapalı (`PDFPLUMBER_AVAILABLE`) |
| PyInstaller | ≥5.0.0 | EXE |
| Tkinter | stdlib | Varsayılan UI / EXE |
| PySide6 | requirements’ta **yok** | Sadece `ui_pyside` suite; ayrıca kurulmalı |

Ağ: `https://www.tcmb.gov.tr/kurlar/{YYYYMM}/{ddMMyyyy}.xml` → USD `ForexBuying`.

---

## Critical Implementation Rules

### Language-Specific Rules

- Yeni iş kuralı / Excel dönüşümü → `isle_fatura_dosyasi` veya yardımcılarına; UI’ya kopyalama.
- Ortak giriş noktası: `run_gelir_export(...)` → `(path, warn | None, summary)`. Tk ve PySide **yalnızca bunu** çağırmalı.
- Ham Excel: sütunlar **başlık adına** (`_resolve_ham_excel_columns` / `_HAM_EXCEL_SUTUN_ALIAS`). Fazla sütunlar yok sayılır; zorunlu başlık yoksa `ValueError`. `iloc` indeksine güvenme.
- Tarih sütunu datetime değilse `pd.to_datetime(..., dayfirst=True, errors="coerce")`.
- Sayısal kolonlar `_coerce_numeric_columns` ile `pd.to_numeric(errors="coerce")` + fill; dtype karışımını önle.
- PDF extract’ler try/except + `None`; çağıran map’e yalnızca başarılı değerleri koy.
- TCMB: HTTP yanıtı yoksa (network/SSL) **eski güne düşme**, `None` dön. Yalnızca HTTP ≠ 200 veya kur yoksa gün geri.
- SSL fallback (`_create_unverified_context`) **sadece** TCMB isteği için; başka yere taşıma.
- Print log’ları iş izleme için kullanılıyor; PySide stdout’u yakalar — anlamlı `print` tut.

### Framework-Specific Rules

- **İki UI, tek motor:** `GelirHazirlamaApp` (Tk) ve `GelirPage` (PySide) iş mantığı yazmaz; sadece dosya seçimi + `run_gelir_export`.
- Tk işlem **senkron** (`root.update`); ağır iş eklerken UI donmasını dikkate al veya PySide pattern’ine (QThread) bak.
- PySide: `_GelirWorker` + `QThread`; yeni parametreler worker `__init__` → `run_gelir_export` zincirine eklenmeli.
- EXE (`build_exe.bat` / `.spec`) yalnızca `gelirhazirlama.py` paketler — `ui_pyside` / PySide **dahil değil**.
- Çıktı dosya adı: `gelir_kalemleri_{ay_dosya}_{yil}_çalışma.xlsx`; `ay_dosya` = `AY_ADI_DOSYA_MAP` (ASCII, örn. EYLÜL→eylul). Map’e yeni ay eklerken her iki UI ay listesini de güncelle.
- Excel kaydı: önce `to_excel`, sonra openpyxl ile SUM + Özel Açıklama kırmızı + sipariş **U=21 / V=22**. Sipariş alanlarını çıktı kolon sırasının ortasına sokma; U/V sabit kalsın.
- PDF içerik map anahtarı: `fatura_no.strip().upper()` **birebir**. Rename’de rakam fallback ayrı; ambiguity’de rename yok.
- PDF rename: UI önce onay sorar (`rename_pdfs`); Hayır’da içerik eşlemesi sürer, dosya adı değişmez. Varsayılan API `rename_pdfs=True` (eski davranış).
- PDF rename kaynak klasörde kalıcı yan etkidir; sessizce “iyileştirme” olarak genişletme.
- Varsayılan ay/yıl: `_default_ay_yil()` (sistem tarihi). Excel seçilince ilk hücre yine override eder.

### Testing Rules

- Otomatik test suite yok; değişiklik sonrası manuel senaryoları çalıştır:
  - USD / TL / EURO döviz
  - İADE (Durum’ta `İADE`) → USD=0 + Özel Açıklama
  - KDV TL==0 + PDF istisna
  - AWSOLS + `Not: Fatura Açıklaması`
  - Çok satırlı fatura açıklama birleşimi
  - PDF rename + AMBIGUOUS (aynı rakam, farklı prefix)
  - Çıktı dosyası açıkken → timestamp’li yedek + warn
  - TCMB erişimsiz → kur boş / log uyarısı, crash yok
- Yeni kural eklerken en az bir olumlu ve bir kenar senaryo doğrula.

### Code Quality & Style Rules

- UI metinleri Türkçe; kod tanımlayıcıları mevcut karışıma uy (Türkçe fonksiyon adları: `isle_fatura_dosyasi`, `extract_*`).
- Büyük yeni özellik için `gelirhazirlama.py`’yi daha fazla şişirmek yerine yardımcı fonksiyon / modül ayırmayı tercih et; UI ayrımı zaten `ui_pyside` pattern’inde.
- Docstring’leri mevcut stil: kısa Türkçe açıklama + parametre anlamı.
- Blocklist ürün metinleri birebir: `"INSURANCE COST"`, `"FREIGHT COST"` — case/fuzzy genişletme yapma unless istenirse.
- AWSOLS firma karşılaştırması: `str(firma).strip().upper() == "AWSOLS"`.

### Development Workflow Rules

- Çalıştırma: `.venv` + `run_app.bat` / `python gelirhazirlama.py`.
- EXE: `build_exe.bat` → `dist\GelirHazirlama.exe`.
- Commit yalnızca kullanıcı isterse; secret / `.venv` / `dist` / `assets` commit etme.
- Bağımlılık eklerken `requirements.txt` ve gerekirse `build_exe.bat` pip listesini / hidden-import’u güncelle. PySide suite için requirements’a eklemeden önce kullanıcıya sor (EXE kapsamı değişir).
- İnsan bağlamı: `docs/NOT_DEFTERI.md`; AI mimari: `docs/architecture.md`. İş kuralı değişince her ikisini de güncelle.

### Critical Don't-Miss Rules

1. **Ham Excel başlık eşlemesi.** Alias listesi (`_HAM_EXCEL_SUTUN_ALIAS`) güncel tutulmalı; `iloc` kullanma.
2. **İş mantığını UI’ya kopyalama** — her zaman `run_gelir_export`.
3. **PDF map ≠ PDF rename eşleme:** map birebir; rename rakam fallback + ambiguity.
4. **İADE tespiti:** `Durum.str.upper().str.contains("İADE")` — Türkçe İ; `IADE` ASCII arama ekleme unless bilinçli.
5. **TRL ve TRY** yerel/USD-EURO ayrımında “yerel” (EURO’ya gitmez).
6. **TL ≈ USD (<0.01)** → USD alanları 0; sonra TCMB yolları (USD/boş döviz) yeniden doldurabilir — sıra önemli.
7. **Kur vs Kur MB:** `Kur` iş kurallarına bağlı; `Kur MB` tüm satırlar için bağımsız TCMB cache.
8. **`ay_adi_dosya` parametresi** `isle_fatura_dosyasi` imzasında var; dosya adı asıl `run_gelir_export` içinde map’ten üretilir — imzayı bozmadan kullan.
9. **Özel Açıklama:** KDV0 istisna + İADE `\n` ile birleşebilir; kırmızı font yalnızca dolu hücreler.
10. **PermissionError** → timestamp’li dosya + kullanıcıya warn string; sessiz overwrite yok.
11. TCMB = urllib; `requests` bağımlılığı yok.
12. **assets/, dist/, build/, .venv** gitignore’da; belgeleme veya kod için varsayma.

---

## Usage Guidelines

**For AI Agents:**

- Kod yazmadan önce bu dosyayı oku; iş kuralı ayrıntısı için `docs/NOT_DEFTERI.md` ve `docs/architecture.md`.
- Tüm kurallara uy; şüphede daha kısıtlayıcı seçeneği tercih et.
- Yeni kalıcı pattern çıkarsa bu dosyayı güncelle.

**For Humans:**

- Dosyayı kısa tut; agent’a özel tut.
- Stack veya iş kuralı değişince güncelle.
- Barizleşen kuralları zamanla çıkar.

Last Updated: 2026-07-12
