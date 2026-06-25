#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Оркестратор: XML поставщика + опт-цены -> наша Google-таблица + public/feed.xml.

Запуск:
  python3 run.py                 # полный прогон (таблица + фид)
  python3 run.py --no-sheets     # только собрать локальный feed.xml (без записи в таблицу)
  python3 run.py --no-opt        # без чтения опт-цен (для отладки парсинга)
"""

import argparse
import os
import sys

import build_feed
import parse_dasmart

HERE = os.path.dirname(os.path.abspath(__file__))
SA_JSON = os.environ.get(
    "GOOGLE_SERVICE_ACCOUNT_JSON", os.path.join(HERE, "service_account.json")
)
OUT_FEED = os.environ.get("OUT_FEED", os.path.join(HERE, "public", "feed.xml"))

_GC = None


def gspread_client():
    """Ленивая инициализация gspread-клиента (один на прогон)."""
    global _GC
    if _GC is None:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(SA_JSON, scopes=scopes)
        _GC = gspread.authorize(creds)
    return _GC


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-sheets", action="store_true",
                    help="не писать в Google-таблицу")
    ap.add_argument("--no-opt", action="store_true",
                    help="не читать опт-цены (отладка)")
    ap.add_argument("--local", action="store_true",
                    help="локальный прогон (для совместимости с CLI)")
    args = ap.parse_args()

    print("Скачивание XML поставщика...", flush=True)
    xml = parse_dasmart.fetch_xml()
    print(f"  получено {len(xml) / 1e6:.1f} МБ", flush=True)

    print("Разбор...", flush=True)
    categories, products = parse_dasmart.parse_feed(xml)
    print(f"  категорий: {len(categories)}, товаров: {len(products)}", flush=True)
    if not products:
        print("ОШИБКА: 0 товаров — прерываю (таблица и фид не трогаются).",
              file=sys.stderr)
        sys.exit(1)

    # --- опт-цены ---
    opt = {}
    if not args.no_opt:
        print("Чтение опт-цен из прайса поставщика...", flush=True)
        import opt_prices
        opt = opt_prices.load_opt_prices(gspread_client())
        print(f"  опт-цен в прайсе: {len(opt)}", flush=True)

    matched = 0
    for p in products:
        v = opt.get(p["vendorCode"], "")
        p["opt"] = v
        if v:
            matched += 1
    print(f"  товаров с опт-ценой: {matched} / {len(products)}", flush=True)

    # --- запись в таблицу ---
    if not args.no_sheets:
        print("Запись в Google-таблицу (Товари + Категорії)...", flush=True)
        import to_sheets
        n = to_sheets.write_all(gspread_client(), products, categories)
        print(f"  записано товаров: {n}", flush=True)

    # --- сборка фида ---
    print("Сборка feed.xml...", flush=True)
    build_feed.write_feed(categories, products, OUT_FEED)
    size = os.path.getsize(OUT_FEED)
    print(f"  {OUT_FEED} ({size / 1e6:.1f} МБ)", flush=True)
    print("Готово.", flush=True)


if __name__ == "__main__":
    main()
