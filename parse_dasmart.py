#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скачивание и потоковый разбор XML-фида поставщика dasmart.com.ua.

Из каждого <offer> берём все поля, КРОМЕ <name_ua> и <description_ua>
(оставляем русские <name>/<description>). Возвращаем категории и товары.
"""

import io
import os
import re
import time
import urllib.request
from xml.etree import ElementTree as ET

FEED_URL = os.environ.get(
    "DASMART_FEED_URL",
    "https://dasmart.com.ua/content/export/e7052aba0549f32c1a825bf48539397b.xml",
)
UA = "Mozilla/5.0 (compatible; dasmart-parser/1.0)"


def fetch_xml(url=FEED_URL, tries=4):
    """Скачать фид (с повторами при кратковременной недоступности)."""
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            last = e
            if i < tries - 1:
                time.sleep(3 * (i + 1))
    raise last


def _strip_doctype(xml):
    # убрать <!DOCTYPE ... shops.dtd>, чтобы парсер не трогал внешний DTD
    return re.sub(r"<!DOCTYPE[^>]*>", "", xml, count=1)


def _text(elem, tag):
    c = elem.find(tag)
    if c is not None and c.text:
        return c.text.strip()
    return ""


def _parse_offer(elem):
    pictures = [
        c.text.strip()
        for c in elem.findall("picture")
        if c.text and c.text.strip()
    ]
    params = []
    for p in elem.findall("param"):
        name = (p.get("name") or "").strip()
        val = (p.text or "").strip()
        if name and val:
            params.append([name, val])
    return {
        "id": (elem.get("id") or "").strip(),
        "group_id": (elem.get("group_id") or "").strip(),
        # available переносим как есть (у поставщика сейчас пусто)
        "available": elem.get("available") or "",
        "vendorCode": _text(elem, "vendorCode"),
        "vendor": _text(elem, "vendor"),
        "name": _text(elem, "name"),
        "description": _text(elem, "description"),
        "price": _text(elem, "price"),
        "oldprice": _text(elem, "oldprice"),
        "currencyId": _text(elem, "currencyId") or "UAH",
        "categoryId": _text(elem, "categoryId"),
        "quantity_in_stock": _text(elem, "quantity_in_stock"),
        "url": _text(elem, "url"),
        "pictures": pictures,
        "params": params,
    }


def parse_feed(xml):
    """Вернуть (categories, products).

    categories: [{"id","parent","name"}], products: [dict из _parse_offer].
    Парсим потоково (iterparse) — не держим весь DOM в памяти.
    """
    xml = _strip_doctype(xml)
    src = io.BytesIO(xml.encode("utf-8"))
    categories = []
    products = []
    for _event, elem in ET.iterparse(src, events=("end",)):
        tag = elem.tag
        if tag == "category":
            categories.append({
                "id": (elem.get("id") or "").strip(),
                "parent": (elem.get("parentId") or "").strip(),
                "name": (elem.text or "").strip(),
            })
        elif tag == "offer":
            products.append(_parse_offer(elem))
            elem.clear()
    return categories, products


if __name__ == "__main__":  # быстрая локальная проверка
    data = fetch_xml()
    cats, prods = parse_feed(data)
    print(f"категорий: {len(cats)}, товаров: {len(prods)}")
    if prods:
        p = prods[0]
        print("пример товара:", p["id"], p["vendorCode"], "|", p["name"][:60])
        print("фото:", len(p["pictures"]), "характеристик:", len(p["params"]))
