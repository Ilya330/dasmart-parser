#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Чтение оптовых цен из прайс-таблицы поставщика (Google Sheets).

Берём строго колонку «Акційна Оптова ціна», ключ — «Артикул» (= vendorCode).
Колонки ищем по названиям в шапке (устойчиво к перестановке столбцов).
Строки-категории (без артикула/цены) отсеиваются сами.
"""

import os
import re

PRICE_SHEET_ID = os.environ.get(
    "PRICE_SHEET_ID", "1GbDWdKB2LY19v5EYwH9vrGm_7CWD8lqbnTLNIPVp0dU"
)
PRICE_WORKSHEET = os.environ.get("PRICE_WORKSHEET", "")  # пусто = первый лист

ARTICLE_HEADER = "Артикул"
OPT_HEADER = "Акційна Оптова ціна"


def norm_price(s):
    """'1 290,00' -> '1290'  (целое без дробной, либо с 2 знаками)."""
    s = str(s).replace("\xa0", "").replace(" ", "").strip()
    s = s.replace(",", ".")
    s = re.sub(r"[^\d.]", "", s)
    if not s:
        return ""
    try:
        v = float(s)
    except ValueError:
        return ""
    if v <= 0:
        return ""
    return str(int(v)) if v == int(v) else f"{v:.2f}"


def _find_header_row(rows):
    for i, r in enumerate(rows[:15]):
        if any(str(c).strip() == ARTICLE_HEADER for c in r):
            return i
    return None


def load_opt_prices(gc, sheet_id=PRICE_SHEET_ID, worksheet=PRICE_WORKSHEET):
    sh = gc.open_by_key(sheet_id)
    ws = sh.worksheet(worksheet) if worksheet else sh.sheet1
    rows = ws.get_all_values()

    hdr_idx = _find_header_row(rows)
    if hdr_idx is None:
        raise RuntimeError(f"В прайсе не найдена колонка '{ARTICLE_HEADER}'")
    hdr = [str(c).strip() for c in rows[hdr_idx]]
    if ARTICLE_HEADER not in hdr:
        raise RuntimeError(f"Нет колонки '{ARTICLE_HEADER}'")
    if OPT_HEADER not in hdr:
        raise RuntimeError(f"Нет колонки '{OPT_HEADER}'")
    art_col = hdr.index(ARTICLE_HEADER)
    opt_col = hdr.index(OPT_HEADER)

    out = {}
    for r in rows[hdr_idx + 1:]:
        if len(r) <= max(art_col, opt_col):
            continue
        art = str(r[art_col]).strip()
        if not art:
            continue
        price = norm_price(r[opt_col])
        if price:
            out[art] = price
    return out
