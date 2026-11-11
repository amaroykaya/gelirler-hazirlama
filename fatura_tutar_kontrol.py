"""
Fatura tutar kontrolü — gelir kalemleri Excel ↔ siparişler Excel karşılaştırması.

Gelir hazırlama akışına dokunmaz.
Fatura tarafı: gelir_kalemleri_*.xlsx (Fatura No + KDV siz Dolar hazır sütunlar).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from openpyxl.styles import Font, PatternFill

from gelirhazirlama import _normalize_col_name

# Gelir kalemleri Excel
_GELIR_FATURA_NO_ALIAS = (
    "fatura no",
    "fatura numarası",
    "fatura numarasi",
    "fatura sıra",
    "fatura sira",
)
_GELIR_KDV_SIZ_DOLAR_ALIAS = (
    "kdv siz dolar",
    "kdv'siz dolar",
    "kdvsiz dolar",
)
_GELIR_FIRMA_ALIAS = (
    "firma",
)

# Sipariş Excel
_SIPARIS_FATURA_NO_ALIAS = (
    "fatura durumu",  # içerik = fatura no
    "fatura no",
    "fatura numarası",
    "fatura numarasi",
)
_SIPARIS_TOPLAM_ALIAS = (
    "toplam fiyat",
)


@dataclass
class FaturaKontrolSatir:
    fatura_no: str
    firma: str
    satis_kdv_siz: Optional[float]
    siparis_toplam: Optional[float]
    fark: Optional[float]
    sonuc: str  # "OK" | "UYARI" | "YOK"


def _find_col(df: pd.DataFrame, aliases: tuple, *, required: bool = True) -> Optional[str]:
    norm_map = {}
    for col in df.columns:
        key = _normalize_col_name(col)
        if key and key not in norm_map:
            norm_map[key] = col
    for alias in aliases:
        a = _normalize_col_name(alias)
        if a in norm_map:
            return norm_map[a]
    if required:
        raise ValueError(
            "Excel'de zorunlu sütun bulunamadı.\n"
            f"Aranan: {', '.join(aliases)}\n"
            f"Dosyadaki başlıklar: {', '.join(str(c) for c in list(df.columns)[:40])}"
        )
    return None


def _para(x) -> Optional[float]:
    if pd.isna(x):
        return None
    if isinstance(x, (int, float, np.floating, np.integer)):
        return round(float(x), 2)
    s = str(x).strip().replace(" ", "").replace(",", ".")
    if not s:
        return None
    try:
        return round(float(s), 2)
    except ValueError:
        return None


def _fatura_key(x) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip().upper()


def load_gelir_faturalar(excel_path: str) -> Dict[str, dict]:
    """
    gelir_kalemleri Excel → {FATURA_NO: {firma, kdv_siz_dolar, fatura_no}}.
    TOPLAM / boş fatura no satırları atlanır.
    """
    raw = pd.read_excel(excel_path)
    col_fno = _find_col(raw, _GELIR_FATURA_NO_ALIAS)
    col_kdv = _find_col(raw, _GELIR_KDV_SIZ_DOLAR_ALIAS)
    col_firma = _find_col(raw, _GELIR_FIRMA_ALIAS, required=False)

    out: Dict[str, dict] = {}
    for i in range(len(raw)):
        fno_raw = raw.iloc[i][col_fno]
        key = _fatura_key(fno_raw)
        if not key:
            continue
        # Dip TOPLAM satırı vb.
        if key in ("TOPLAM", "TOTAL"):
            continue
        kdv_siz = _para(raw.iloc[i][col_kdv])
        firma = ""
        if col_firma is not None:
            f = raw.iloc[i][col_firma]
            firma = "" if pd.isna(f) else str(f).strip()
            if _normalize_col_name(firma) == "toplam":
                continue

        if key in out:
            prev = out[key]["kdv_siz_dolar"]
            if prev is not None and kdv_siz is not None:
                out[key]["kdv_siz_dolar"] = round(prev + kdv_siz, 2)
            elif kdv_siz is not None:
                out[key]["kdv_siz_dolar"] = kdv_siz
            if not out[key]["firma"] and firma:
                out[key]["firma"] = firma
        else:
            out[key] = {
                "firma": firma,
                "kdv_siz_dolar": kdv_siz,
                "fatura_no": str(fno_raw).strip(),
            }
    return out


def load_siparis_toplamlar(excel_path: str) -> Dict[str, float]:
    """
    Sipariş Excel → {FATURA_NO: Toplam Fiyat toplamı}.
    Fatura Durumu boş olan satırlar atlanır.
    """
    raw = pd.read_excel(excel_path)
    col_fno = _find_col(raw, _SIPARIS_FATURA_NO_ALIAS)
    col_top = _find_col(raw, _SIPARIS_TOPLAM_ALIAS)

    totals: Dict[str, float] = {}
    for i in range(len(raw)):
        key = _fatura_key(raw.iloc[i][col_fno])
        if not key:
            continue
        tutar = _para(raw.iloc[i][col_top])
        if tutar is None:
            continue
        totals[key] = round(totals.get(key, 0.0) + tutar, 2)
    return totals


def karsilastir_fatura_tutarlari(
    gelir_excel: str,
    siparis_excel: str,
) -> Tuple[List[FaturaKontrolSatir], dict]:
    """
    Gelir kalemleri faturalarını sürücü alarak siparişlerle karşılaştırır.
    Dönüş: (satırlar, özet sayılar)
    """
    if not Path(gelir_excel).is_file():
        raise FileNotFoundError(f"Gelir kalemleri Excel bulunamadı: {gelir_excel}")
    if not Path(siparis_excel).is_file():
        raise FileNotFoundError(f"Sipariş Excel bulunamadı: {siparis_excel}")

    gelir = load_gelir_faturalar(gelir_excel)
    siparis = load_siparis_toplamlar(siparis_excel)

    rows: List[FaturaKontrolSatir] = []
    n_ok = n_uyari = n_yok = 0
    for key in sorted(gelir.keys()):
        info = gelir[key]
        s_tutar = info["kdv_siz_dolar"]
        if key not in siparis:
            rows.append(
                FaturaKontrolSatir(
                    fatura_no=info["fatura_no"],
                    firma=info["firma"],
                    satis_kdv_siz=s_tutar,
                    siparis_toplam=None,
                    fark=None,
                    sonuc="YOK",
                )
            )
            n_yok += 1
            continue
        p_tutar = siparis[key]
        if s_tutar is None:
            rows.append(
                FaturaKontrolSatir(
                    fatura_no=info["fatura_no"],
                    firma=info["firma"],
                    satis_kdv_siz=None,
                    siparis_toplam=p_tutar,
                    fark=None,
                    sonuc="UYARI",
                )
            )
            n_uyari += 1
            continue
        fark = round(s_tutar - p_tutar, 2)
        if fark == 0:
            sonuc = "OK"
            n_ok += 1
        else:
            sonuc = "UYARI"
            n_uyari += 1
        rows.append(
            FaturaKontrolSatir(
                fatura_no=info["fatura_no"],
                firma=info["firma"],
                satis_kdv_siz=s_tutar,
                siparis_toplam=p_tutar,
                fark=fark,
                sonuc=sonuc,
            )
        )

    stats = {
        "toplam": len(rows),
        "ok": n_ok,
        "uyari": n_uyari,
        "yok": n_yok,
        "gelir_fatura": len(gelir),
        "siparis_fatura_no": len(siparis),
    }
    return rows, stats


def kaydet_kontrol_excel(
    rows: List[FaturaKontrolSatir],
    stats: dict,
    output_folder: str,
    *,
    gelir_excel: str = "",
    siparis_excel: str = "",
) -> str:
    """
    Kontrol sonucunu Excel olarak kaydeder.
    Dönüş: kaydedilen dosya yolu.
    Sayfalar: Sonuç (tüm satırlar), Özet (sayılar + kaynak dosyalar).
    """
    out_dir = Path(output_folder)
    if not out_dir.is_dir():
        raise FileNotFoundError(f"Çıktı klasörü bulunamadı: {output_folder}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"fatura_tutar_kontrol_{stamp}.xlsx"

    detail = pd.DataFrame(
        [
            {
                "Fatura No": r.fatura_no,
                "Firma": r.firma,
                "Gelir KDV siz Dolar": r.satis_kdv_siz,
                "Sipariş Toplam Fiyat": r.siparis_toplam,
                "Fark": r.fark,
                "Sonuç": r.sonuc,
            }
            for r in rows
        ]
    )
    ozet = pd.DataFrame(
        [
            {"Alan": "Kontrol tarihi", "Değer": datetime.now().strftime("%d.%m.%Y %H:%M")},
            {"Alan": "Gelir kalemleri dosyası", "Değer": Path(gelir_excel).name if gelir_excel else ""},
            {"Alan": "Siparişler dosyası", "Değer": Path(siparis_excel).name if siparis_excel else ""},
            {"Alan": "Kontrol edilen fatura", "Değer": stats.get("toplam", 0)},
            {"Alan": "OK", "Değer": stats.get("ok", 0)},
            {"Alan": "UYARI (fark)", "Değer": stats.get("uyari", 0)},
            {"Alan": "YOK (siparişte yok)", "Değer": stats.get("yok", 0)},
            {"Alan": "Siparişte benzersiz fatura no", "Değer": stats.get("siparis_fatura_no", 0)},
        ]
    )

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        detail.to_excel(writer, sheet_name="Sonuç", index=False)
        ozet.to_excel(writer, sheet_name="Özet", index=False)
        ws = writer.sheets["Sonuç"]
        fill_uyari = PatternFill(start_color="FFFBEB", end_color="FFFBEB", fill_type="solid")
        fill_yok = PatternFill(start_color="FEF2F2", end_color="FEF2F2", fill_type="solid")
        font_uyari = Font(color="92400E")
        font_yok = Font(color="991B1B")
        font_ok = Font(color="166534")
        sonuc_col = 6  # Sonuç
        for i, r in enumerate(rows, start=2):
            cell = ws.cell(row=i, column=sonuc_col)
            if r.sonuc == "OK":
                cell.font = font_ok
            elif r.sonuc == "UYARI":
                cell.font = font_uyari
                for c in range(1, 7):
                    ws.cell(row=i, column=c).fill = fill_uyari
            elif r.sonuc == "YOK":
                cell.font = font_yok
                for c in range(1, 7):
                    ws.cell(row=i, column=c).fill = fill_yok

    return str(out_path)


def run_fatura_tutar_kontrol(
    gelir_excel: str,
    siparis_excel: str,
    output_folder: str,
) -> Tuple[str, List[FaturaKontrolSatir], dict]:
    """Karşılaştır + Excel kaydet. Dönüş: (çıktı yolu, satırlar, stats)."""
    rows, stats = karsilastir_fatura_tutarlari(gelir_excel, siparis_excel)
    path = kaydet_kontrol_excel(
        rows,
        stats,
        output_folder,
        gelir_excel=gelir_excel,
        siparis_excel=siparis_excel,
    )
    stats["cikti_yolu"] = path
    return path, rows, stats
