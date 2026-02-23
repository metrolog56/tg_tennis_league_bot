"""
Планировщик: ежедневная проверка последнего дня месяца и закрытие тура.
APScheduler, задача в 23:55.
"""
import calendar
import logging
import os
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)
_scheduler: Optional[AsyncIOScheduler] = None
_bot: Optional["Bot"] = None

MONTH_NAMES = [
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]
DIVISION_COEFS = {1: 0.30, 2: 0.27, 3: 0.25, 4: 0.22}


def _get_client():
    from services.supabase_client import _get_client as get
    return get()


def _is_last_day_of_month() -> bool:
    now = datetime.now(timezone.utc)
    _, last = calendar.monthrange(now.year, now.month)
    return now.day == last


async def close_tour(bot: Optional["Bot"] = None) -> str:
    """
    1. Найти активный сезон
    2. pending матчи → not_played, 0-0
    3. По каждому дивизиону: позиции (очки, разница сетов)
    4. Обновить position в division_players
    5. Рейтинг уже обновляется после каждого матча
    6. season.status = 'closed'
    7. Сообщение в Telegram ADMIN_TELEGRAM_ID с итогами
    """
    client = _get_client()
    season_r = (
        client.table("seasons")
        .select("*")
        .eq("status", "active")
        .order("year", desc=True)
        .order("month", desc=True)
        .limit(1)
        .execute()
    )
    if not season_r.data or len(season_r.data) == 0:
        return "Нет активного сезона."

    season = season_r.data[0]
    season_id = season["id"]
    season_name = season.get("name", "")

    # 2. Все pending матчи в дивизионах этого сезона → not_played, 0-0
    divs_r = client.table("divisions").select("id").eq("season_id", season_id).execute()
    for d in divs_r.data or []:
        client.table("matches").update({
            "status": "not_played",
            "sets_player1": 0,
            "sets_player2": 0,
        }).eq("division_id", d["id"]).eq("status", "pending").execute()

    # 3–4. Позиции в каждом дивизионе: очки → личная встреча → разница сетов
    lines = [f"📋 <b>Тур закрыт: {season_name}</b>\n"]
    for d in divs_r.data or []:
        div_id = d["id"]
        dps_r = (
            client.table("division_players")
            .select("id, player_id, total_points, total_sets_won, total_sets_lost")
            .eq("division_id", div_id)
            .execute()
        )
        rows = dps_r.data or []
        if not rows:
            continue
        matches_r = (
            client.table("matches")
            .select("player1_id, player2_id, sets_player1, sets_player2")
            .eq("division_id", div_id)
            .eq("status", "played")
            .execute()
        )
        matches = matches_r.data or []

        def sort_key(r):
            pts = r.get("total_points") or 0
            sw = r.get("total_sets_won") or 0
            sl = r.get("total_sets_lost") or 0
            return (-pts, -(sw - sl))

        rows.sort(key=sort_key)

        i = 0
        while i < len(rows):
            j = i
            while j < len(rows) and sort_key(rows[j]) == sort_key(rows[i]):
                j += 1
            if j - i > 1:
                group = rows[i:j]
                group_ids = {r["player_id"] for r in group}
                wins = {r["player_id"]: 0 for r in group}
                for m in matches:
                    p1, p2 = m["player1_id"], m["player2_id"]
                    if p1 not in group_ids or p2 not in group_ids:
                        continue
                    s1, s2 = m.get("sets_player1") or 0, m.get("sets_player2") or 0
                    if s1 > s2:
                        wins[p1] = wins.get(p1, 0) + 1
                    elif s2 > s1:
                        wins[p2] = wins.get(p2, 0) + 1
                group.sort(key=lambda r: wins.get(r["player_id"], 0), reverse=True)
                rows[i:j] = group
            i = j

        for pos, row in enumerate(rows, 1):
            client.table("division_players").update({"position": pos}).eq("id", row["id"]).execute()
        div_num_r = client.table("divisions").select("number").eq("id", div_id).execute()
        div_num = div_num_r.data[0].get("number", "") if div_num_r.data else ""
        dp_player_ids = [r["player_id"] for r in rows]
        names_r = client.table("players").select("id, name").in_("id", dp_player_ids).execute()
        id_to_name = {p["id"]: p["name"] for p in (names_r.data or [])}
        lines.append(f"\n<b>Дивизион {div_num}</b>")
        for pos, row in enumerate(rows, 1):
            name = id_to_name.get(row["player_id"], "—")
            pts = row.get("total_points") or 0
            lines.append(f"  {pos}. {name} — {pts} очк.")

    # 6. Закрыть сезон
    client.table("seasons").update({"status": "closed"}).eq("id", season_id).execute()

    report = "\n".join(lines)

    # 7. Сообщение админу
    admin_id = os.getenv("ADMIN_TELEGRAM_ID")
    if admin_id and bot:
        try:
            await bot.send_message(int(admin_id.strip()), report)
        except Exception as e:
            logger.warning("Не удалось отправить отчёт админу: %s", e)

    return report


def prepare_next_season() -> Optional[str]:
    """
    Создать следующий сезон с ротацией:
    топ-2 из дивизиона N → дивизион N-1, последние 2 → N+1.
    Если в дивизионе >8 игроков — двигать по 3.
    """
    client = _get_client()
    closed_r = (
        client.table("seasons")
        .select("*")
        .eq("status", "closed")
        .order("year", desc=True)
        .order("month", desc=True)
        .limit(1)
        .execute()
    )
    if not closed_r.data:
        return None
    closed = closed_r.data[0]
    year, month = closed["year"], closed["month"]
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1
    next_name = f"{MONTH_NAMES[next_month]} {next_year}"

    new_season_r = client.table("seasons").insert({
        "year": next_year,
        "month": next_month,
        "name": next_name,
        "status": "active",
    }).select().execute()
    if not new_season_r.data:
        return None
    new_season_id = new_season_r.data[0]["id"]

    old_divs_r = (
        client.table("divisions")
        .select("id, number")
        .eq("season_id", closed["id"])
        .order("number")
        .execute()
    )
    old_divs = {d["number"]: d["id"] for d in (old_divs_r.data or [])}
    if not old_divs:
        return new_season_id

    nums = sorted(old_divs.keys())
    new_div_ids = {}
    for num in nums:
        coef = DIVISION_COEFS.get(num, 0.22)
        r = client.table("divisions").insert({
            "season_id": new_season_id,
            "number": num,
            "coef": coef,
        }).select().execute()
        if r.data:
            new_div_ids[num] = r.data[0]["id"]

    # По каждому старому дивизиону: разбить на promoted, stay, relegated
    def get_ordered_players(division_id):
        r = (
            client.table("division_players")
            .select("player_id, position, total_points, total_sets_won, total_sets_lost")
            .eq("division_id", division_id)
            .execute()
        )
        rows = r.data or []
        # 1 = лучший: сначала по position, затем по очкам и разнице сетов
        rows.sort(key=lambda x: (x.get("position") or 99, -(x.get("total_points") or 0), -((x.get("total_sets_won") or 0) - (x.get("total_sets_lost") or 0))))
        return [x["player_id"] for x in rows]

    for num in nums:
        old_div_id = old_divs[num]
        new_div_id = new_div_ids.get(num)
        if not new_div_id:
            continue
        player_ids = get_ordered_players(old_div_id)
        n = len(player_ids)
        move_count = 3 if n > 8 else 2
        promoted = player_ids[:move_count]
        relegated = player_ids[-move_count:] if n >= move_count else []
        stay = player_ids[move_count:n - move_count] if n > 2 * move_count else []

        # В новый дивизион num попадают: stay + relegated из (num-1) + promoted из (num+1)
        into_this = list(stay)
        if num - 1 in old_divs:
            prev_players = get_ordered_players(old_divs[num - 1])
            prev_n = len(prev_players)
            prev_move = 3 if prev_n > 8 else 2
            into_this.extend(prev_players[-prev_move:] if prev_n >= prev_move else [])
        if num + 1 in old_divs:
            next_players = get_ordered_players(old_divs[num + 1])
            next_move = 3 if len(next_players) > 8 else 2
            into_this.extend(next_players[:next_move])

        for pid in into_this:
            try:
                client.table("division_players").insert({
                    "division_id": new_div_id,
                    "player_id": pid,
                }).execute()
            except Exception:
                pass

    return new_season_id


async def _daily_check(bot: Optional["Bot"] = None) -> None:
    if not _is_last_day_of_month():
        return
    logger.info("Last day of month: running close_tour")
    try:
        report = await close_tour(bot)
        logger.info("close_tour done: %s", report[:200])
        next_season_id = prepare_next_season()
        if next_season_id:
            logger.info("prepare_next_season done: %s", next_season_id)
    except Exception as e:
        logger.exception("close_tour failed: %s", e)


def start_scheduler(bot: Optional["Bot"] = None) -> None:
    global _scheduler, _bot
    _bot = bot
    if _scheduler is not None:
        return
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _daily_check,
        CronTrigger(hour=23, minute=55),
        args=[bot],
        id="close_tour_daily",
    )
    _scheduler.start()
    logger.info("Scheduler started (daily 23:55)")
