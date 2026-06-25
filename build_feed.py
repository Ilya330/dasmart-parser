#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка итогового YML-XML фида из распарсенных товаров.

= фид поставщика, но БЕЗ <name_ua>/<description_ua> и С добавленным
<vendorprice> (только если опт-цена известна).
"""

import os
from datetime import datetime
from xml.sax.saxutils import escape

SHOP_NAME = os.environ.get("SHOP_NAME", "dasmart")
SHOP_COMPANY = os.environ.get("SHOP_COMPANY", "dasmart")
SHOP_URL = os.environ.get("SHOP_URL", "https://dasmart.com.ua")
CURRENCY = os.environ.get("CURRENCY", "UAH")


def _esc(s):
    return escape(str(s), {'"': "&quot;"})


def _cdata(s):
    return "<![CDATA[" + str(s).replace("]]>", "]]&gt;") + "]]>"


def build_xml(categories, products):
    out = ['<?xml version="1.0" encoding="UTF-8"?>']
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    out.append(f'<yml_catalog date="{date}">')
    out.append("<shop>")
    out.append(f"<name>{_esc(SHOP_NAME)}</name>")
    out.append(f"<company>{_esc(SHOP_COMPANY)}</company>")
    out.append(f"<url>{_esc(SHOP_URL)}</url>")
    out.append(f'<currencies><currency id="{CURRENCY}" rate="1"/></currencies>')

    out.append("<categories>")
    for c in categories:
        parent = f' parentId="{_esc(c["parent"])}"' if c.get("parent") else ""
        out.append(
            f'<category id="{_esc(c["id"])}"{parent}>{_esc(c["name"])}</category>'
        )
    out.append("</categories>")

    out.append("<offers>")
    for p in products:
        attrs = f' id="{_esc(p.get("id", ""))}"'
        if p.get("group_id"):
            attrs += f' group_id="{_esc(p["group_id"])}"'
        attrs += f' available="{_esc(p.get("available", ""))}"'
        out.append(f"<offer{attrs}>")

        if p.get("url"):
            out.append(f"<url>{_esc(p['url'])}</url>")
        if p.get("price") not in ("", None):
            out.append(f"<price>{_esc(p['price'])}</price>")
        if p.get("oldprice"):
            out.append(f"<oldprice>{_esc(p['oldprice'])}</oldprice>")
        # наш тег: оптовая цена (только если известна)
        if p.get("opt"):
            out.append(f"<vendorprice>{_esc(p['opt'])}</vendorprice>")
        out.append(f"<currencyId>{_esc(p.get('currencyId') or CURRENCY)}</currencyId>")
        if p.get("categoryId"):
            out.append(f"<categoryId>{_esc(p['categoryId'])}</categoryId>")
        if p.get("quantity_in_stock") not in ("", None):
            out.append(
                f"<quantity_in_stock>{_esc(p['quantity_in_stock'])}</quantity_in_stock>"
            )
        if p.get("vendorCode"):
            out.append(f"<vendorCode>{_esc(p['vendorCode'])}</vendorCode>")
        if p.get("vendor"):
            out.append(f"<vendor>{_esc(p['vendor'])}</vendor>")
        if p.get("name"):
            out.append(f"<name>{_cdata(p['name'])}</name>")
        if p.get("description"):
            out.append(f"<description>{_cdata(p['description'])}</description>")
        for u in p.get("pictures", []):
            out.append(f"<picture>{_esc(u)}</picture>")
        for pn, pv in p.get("params", []):
            out.append(f'<param name="{_esc(pn)}">{_esc(pv)}</param>')
        out.append("</offer>")

    out.append("</offers>")
    out.append("</shop>")
    out.append("</yml_catalog>")
    return "\n".join(out)


def write_feed(categories, products, path):
    xml = build_xml(categories, products)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)
    return path
