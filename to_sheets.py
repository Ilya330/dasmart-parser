#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Запись товаров и категорий в нашу Google-таблицу `parsing_dassmart`.

Листы перезаписываются целиком (clear + запись чанками). Колонка «Опт ціна»
заполняется заранее в run.py (поле p["opt"]).
"""

import json
import os

TARGET_SHEET_ID = os.environ.get(
    "TARGET_SHEET_ID", "1Oy16IwAttdteCwIr8QIybXYGLtXhbU73f6JT1X-64vk"
)
PRODUCTS_WS = os.environ.get("PRODUCTS_WORKSHEET", "Товари")
CATEGORIES_WS = os.environ.get("CATEGORIES_WORKSHEET", "Категорії")

CELL_LIMIT = 50000   # лимит символов в ячейке Google Sheets
CHUNK = 400          # строк за один запрос update

HEADERS = [
    "ID", "group_id", "available", "Артикул", "Бренд", "Назва", "Опис",
    "Ціна", "Стара ціна", "Опт ціна", "Валюта", "Категорія ID",
    "Кількість", "Фото", "Характеристики",
]
CAT_HEADERS = ["ID", "Parent ID", "Назва"]


def product_to_row(p):
    desc = p.get("description", "")
    if len(desc) > CELL_LIMIT:
        desc = desc[:CELL_LIMIT]
    photos = "\n".join(p.get("pictures", []))
    params = json.dumps(p.get("params", []), ensure_ascii=False)
    if len(params) > CELL_LIMIT:
        params = params[:CELL_LIMIT]
    return [
        p.get("id", ""), p.get("group_id", ""), p.get("available", ""),
        p.get("vendorCode", ""), p.get("vendor", ""), p.get("name", ""),
        desc, p.get("price", ""), p.get("oldprice", ""), p.get("opt", ""),
        p.get("currencyId", ""), p.get("categoryId", ""),
        p.get("quantity_in_stock", ""), photos, params,
    ]


def _write_sheet(sh, title, headers, rows):
    try:
        ws = sh.worksheet(title)
    except Exception:  # noqa: BLE001  WorksheetNotFound
        ws = sh.add_worksheet(title=title, rows=len(rows) + 10, cols=len(headers))
    ws.clear()
    ws.resize(rows=max(len(rows) + 1, 2), cols=len(headers))

    table = [headers] + rows
    r = 1
    for i in range(0, len(table), CHUNK):
        chunk = table[i:i + CHUNK]
        ws.update(range_name=f"A{r}", values=chunk, value_input_option="RAW")
        r += len(chunk)
    try:
        ws.freeze(rows=1)
    except Exception:  # noqa: BLE001
        pass


def write_all(gc, products, categories, sheet_id=TARGET_SHEET_ID):
    """Записать оба листа за одно открытие таблицы. Вернуть кол-во товаров."""
    sh = gc.open_by_key(sheet_id)
    prod_rows = [product_to_row(p) for p in products]
    _write_sheet(sh, PRODUCTS_WS, HEADERS, prod_rows)
    cat_rows = [[c.get("id", ""), c.get("parent", ""), c.get("name", "")]
                for c in categories]
    _write_sheet(sh, CATEGORIES_WS, CAT_HEADERS, cat_rows)
    return len(prod_rows)
