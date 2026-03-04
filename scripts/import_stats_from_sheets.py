#!/usr/bin/env python3
"""
Одноразовый импорт статистики игроков из CSV (экспорт Google Sheets) в Supabase.
Заполняет / обновляет таблицу manual_player_stats (games, wins) по player_id,
telegram_id или name.

Использование:
  python scripts/import_stats_from_sheets.py path/to/stats.csv

Ожидаемые колонки (любая из комбинаций):
  - Идентификатор игрока:
    * player_id  (UUID из таблицы players)           -- предпочтительно
    * telegram_id / telegramId                       -- телеграм-id
    * Имя / name / Name                              -- имя игрока (должно быть уникальным)
  - Статистика:
    * Игры / games
    * В / wins
    * (опционально) П / losses, % / win_percent      -- сейчас не используются

Если для строки не удаётся однозначно сопоставить игрока, она пропускается.
"""

import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # type: ignore
from supabase import create_client  # type: ignore


def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("Укажите SUPABASE_URL и SUPABASE_KEY (или SUPABASE_SERVICE_KEY) в .env")
        return None
    return create_client(url, key)


def resolve_player_id(sb, row):
    """Вернёт player_id (UUID) или None."""
    # 1) Явный player_id
    pid = (row.get("player_id") or row.get("playerId") or "").strip()
    if pid:
        return pid

    # 2) telegram_id
    tid_raw = (row.get("telegram_id") or row.get("telegramId") or "").strip()
    if tid_raw:
        try:
            tid = int(tid_raw)
        except ValueError:
            print(f"  [warn] Неверный telegram_id '{tid_raw}', пропускаю строку")
            return None
        try:
            r = (
                sb.table("players")
                .select("id, name")
                .eq("telegram_id", tid)
                .execute()
            )
        except Exception as e:
            print(f"  [warn] Ошибка поиска по telegram_id {tid}: {e}")
            return None
        data = getattr(r, "data", None) or []
        if len(data) == 1:
            return data[0]["id"]
        if len(data) == 0:
            print(f"  [warn] Игрок с telegram_id {tid} не найден, пропускаю строку")
            return None
        print(f"  [warn] Несколько игроков с telegram_id {tid}, пропускаю строку")
        return None

    # 3) name (должно быть уникальным)
    name = (
        row.get("Имя")
        or row.get("name")
        or row.get("Name")
        or ""
    ).strip()
    if not name:
        return None
    try:
        r = (
            sb.table("players")
            .select("id, name")
            .eq("name", name)
            .execute()
        )
    except Exception as e:
        print(f"  [warn] Ошибка поиска по name '{name}': {e}")
        return None
    data = getattr(r, "data", None) or []
    if len(data) == 1:
        return data[0]["id"]
    if len(data) == 0:
        print(f"  [warn] Игрок с name '{name}' не найден, пропускаю строку")
        return None
    print(f"  [warn] Несколько игроков с name '{name}', пропускаю строку")
    return None


def parse_int(value, default=0):
    if value is None:
        return default
    s = str(value).strip().replace(",", ".")
    if not s:
        return default
    try:
        return int(float(s))
    except ValueError:
        return default


def main():
    if len(sys.argv) < 2:
        print("Использование: python scripts/import_stats_from_sheets.py <path/to/stats.csv>")
        sys.exit(1)
    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"Файл не найден: {csv_path}")
        sys.exit(1)

    load_dotenv(ROOT / "bot" / ".env")
    sb = get_supabase_client()
    if not sb:
        sys.exit(1)

    total = 0
    updated = 0
    skipped = 0

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            player_id = resolve_player_id(sb, row)
            if not player_id:
                skipped += 1
                continue

            games = parse_int(row.get("Игры") or row.get("games"))
            wins = parse_int(row.get("В") or row.get("wins"))
            if games < 0 or wins < 0:
                print(f"  [warn] Отрицательные значения games/wins для player_id={player_id}, пропускаю")
                skipped += 1
                continue
            if wins > games:
                print(f"  [warn] wins > games для player_id={player_id}, wins={wins}, games={games}, корректирую wins=games")
                wins = games

            payload = {
                "player_id": player_id,
                "games": games,
                "wins": wins,
            }
            try:
                sb.table("manual_player_stats").upsert(payload, on_conflict="player_id").execute()
                updated += 1
                print(f"OK: player_id={player_id} games={games} wins={wins}")
            except Exception as e:
                print(f"Ошибка upsert для player_id={player_id}: {e}")
                skipped += 1

    print(f"\nИмпорт завершён. Всего строк: {total}, обновлено записей: {updated}, пропущено: {skipped}")


if __name__ == "__main__":
    main()

