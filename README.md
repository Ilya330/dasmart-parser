# dasmart-parser

Самообновляемый XML-фид поставщика **dasmart.com.ua** с добавленным тегом
`<vendorprice>` (оптовая цена). Опт-цена берётся из прайс-таблицы поставщика и
сопоставляется с товаром по артикулу (`vendorCode`).

```
XML поставщика ──┐
                 ├─► наша Google-таблица (товары + «Опт ціна») ──► feed.xml ──► Pages-ссылка
прайс (Опт ціна)─┘
```

Обновляется автоматически **3 раза в сутки** через GitHub Actions, результат
публикуется на GitHub Pages. Компьютер включать не нужно.

## Файлы

| Файл | Назначение |
|---|---|
| `parse_dasmart.py` | Скачивание + потоковый разбор XML поставщика (без `name_ua`/`description_ua`) |
| `opt_prices.py` | Чтение опт-цен из прайса (строго «Акційна Оптова ціна») |
| `to_sheets.py` | Запись листов «Товари» и «Категорії» в нашу таблицу |
| `build_feed.py` | Сборка `public/feed.xml` (+ `<vendorprice>`) |
| `run.py` | Оркестратор всего пайплайна |
| `.github/workflows/update.yml` | Расписание 3×/сутки + деплой на Pages |

## Источники данных

- **XML поставщика:** `DASMART_FEED_URL`
  (по умолч. `https://dasmart.com.ua/content/export/e7052aba0549f32c1a825bf48539397b.xml`)
- **Прайс поставщика (опт):** Google-таблица `PRICE_SHEET_ID`
  (`1GbDWdKB2LY19v5EYwH9vrGm_7CWD8lqbnTLNIPVp0dU`), колонки «Артикул» и «Акційна Оптова ціна».
- **Наша таблица:** `TARGET_SHEET_ID` (`1Oy16IwAttdteCwIr8QIybXYGLtXhbU73f6JT1X-64vk`),
  листы «Товари» и «Категорії». Расшарена на сервис-аккаунт
  `sheets-bot@gallary-434015.iam.gserviceaccount.com` (Редактор).

Все ID можно переопределить переменными окружения.

## Локальный запуск

```bash
pip3 install -r requirements.txt          # gspread, google-auth
python3 run.py --no-sheets                 # только собрать public/feed.xml
python3 run.py                             # + записать в Google-таблицу
```

## Развёртывание в GitHub (один раз)

```bash
gh repo create dasmart-parser --public --source=. --remote=origin --push
gh secret set GOOGLE_SERVICE_ACCOUNT_JSON < service_account.json
```

Затем в репозитории: **Settings → Pages → Source: GitHub Actions**.
Запустить вручную: **Actions → Update feed → Run workflow**.

Готовая ссылка фида: `https://<логин>.github.io/dasmart-parser/feed.xml` —
её указываете в импорте Prom.ua / Rozetka.

## Заметки

- **Опт-цена есть не у всех.** Если артикула нет в прайсе — `<vendorprice>` не
  выводится (товар остаётся, просто без опт-цены). Сейчас совпадает ~60%.
- **Фид публичный** (Prom.ua тянет без авторизации) → `<vendorprice>` виден всем,
  у кого есть ссылка.
- **Зеркалирование поставщика.** Таблица и фид полностью пересобираются каждый
  прогон; товары, пропавшие из фида поставщика, исчезают и у нас.
- Если поставщик заменит прайс-таблицу (новый ID/дата в названии) — обновите
  `PRICE_SHEET_ID` и заново расшарьте её на сервис-аккаунт.
