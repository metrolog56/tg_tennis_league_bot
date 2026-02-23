#!/usr/bin/env python3
"""
Одноразовый импорт игроков из CSV (экспорт из Google Sheets) в Supabase.
Создаёт players с name и рейтингом из столбца "Рейтинг"; telegram_id = NULL
(заполнится при первом /start в боте).

Использование:
  python scripts/import_from_sheets.py path/to/export.csv

Формат CSV: заголовок с колонками, среди них — "Имя" (или "name") и "Рейтинг" (или "rating").
Разделитель — запятая. Кодировка — UTF-8.
"""
import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / "bot" / ".env")

from supabase import create_client


def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("Укажите SUPABASE_URL и SUPABASE_KEY (или SUPABASE_SERVICE_KEY) в .env")
        return None
    return create_client(url, key)


def main():
    if len(sys.argv) < 2:
        print("Использование: python scripts/import_from_sheets.py <path/to/file.csv>")
        sys.exit(1)
    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"Файл не найден: {csv_path}")
        sys.exit(1)

    sb = get_supabase_client()
    if not sb:
        sys.exit(1)

    count = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Имя") or row.get("name") or row.get("Name") or "").strip()
            if not name:
                continue
            rating_raw = row.get("Рейтинг") or row.get("rating") or "100"
            try:
                rating = float(rating_raw)
            except ValueError:
                rating = 100.0
            try:
                sb.table("players").insert({
                    "name": name,
                    "rating": round(rating, 2),
                    "telegram_id": None,
                }).execute()
                count += 1
                print(f"OK: {name} (рейтинг {rating})")
            except Exception as e:
                print(f"Ошибка для {name}: {e}")

    print(f"\nИмпорт завершён. Добавлено записей: {count}")


if __name__ == "__main__":
    main()
