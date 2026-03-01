"""
Планировщик: ежедневная проверка последнего дня месяца и закрытие тура;
периодическая рассылка уведомлений о матчах, ожидающих подтверждения.
APScheduler: close_tour в 23:55, pending_confirm уведомления каждые 2 мин.
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

    # 2. Все pending и pending_confirm матчи в дивизионах этого сезона → not_played, 0-0
    divs_r = client.table("divisions").select("id").eq("season_id", season_id).execute()
    for d in divs_r.data or []:
        for status in ("pending", "pending_confirm"):
            client.table("matches").update({
                "status": "not_played",
                "sets_player1": 0,
                "sets_player2": 0,
                "submitted_by": None,
                "notification_sent_at": None,
            }).eq("division_id", d["id"]).eq("status", status).execute()

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
    }).execute()
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
        }).execute()
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


async def _send_pending_confirm_notifications(bot: Optional["Bot"] = None) -> None:
    """
    Найти матчи status=pending_confirm с notification_sent_at IS NULL,
    отправить сопернику (не submitted_by) сообщение со ссылкой на WebApp,
    обновить notification_sent_at.
    """
    if not bot:
        return
    webapp_url = (os.getenv("WEBAPP_URL") or "").strip().rstrip("/")
    if not webapp_url:
        logger.debug("WEBAPP_URL not set, skip pending_confirm notifications")
        return
    try:
        client = _get_client()
        r = (
            client.table("matches")
            .select("id, player1_id, player2_id, sets_player1, sets_player2, submitted_by")
            .eq("status", "pending_confirm")
            .is_("notification_sent_at", "null")
            .execute()
        )
        for m in r.data or []:
            match_id = m["id"]
            submitted_by = m.get("submitted_by")
            p1, p2 = m.get("player1_id"), m.get("player2_id")
            opponent_id = p2 if submitted_by == p1 else p1
            s1 = m.get("sets_player1") or 0
            s2 = m.get("sets_player2") or 0
            score = f"{s1}:{s2}"
            # Имя вносящего
            submitter_r = client.table("players").select("name").eq("id", submitted_by).execute()
            submitter_name = (submitter_r.data or [{}])[0].get("name", "Игрок") if submitter_r.data else "Игрок"
            # telegram_id соперника
            opp_r = client.table("players").select("telegram_id").eq("id", opponent_id).execute()
            if not opp_r.data or opp_r.data[0].get("telegram_id") is None:
                logger.warning("No telegram_id for opponent %s, match %s", opponent_id, match_id)
                continue
            telegram_id = int(opp_r.data[0]["telegram_id"])
            confirm_url = f"{webapp_url}#/confirm-match/{match_id}"
            text = (
                f"{submitter_name} внёс результат вашего матча: {score}. "
                "Подтвердите или отклоните результат."
            )
            try:
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Подтвердить / Отклонить", url=confirm_url)],
                ])
                await bot.send_message(telegram_id, text, reply_markup=kb)
            except Exception as e:
                logger.warning("Failed to send pending_confirm notification to %s: %s", telegram_id, e)
                continue
            now_iso = datetime.now(timezone.utc).isoformat()
            client.table("matches").update({"notification_sent_at": now_iso}).eq("id", match_id).execute()
            logger.info("Sent pending_confirm notification for match %s to player %s", match_id, opponent_id)
    except Exception as e:
        logger.exception("_send_pending_confirm_notifications failed: %s", e)


async def _send_game_request_notifications(bot: Optional["Bot"] = None) -> None:
    """Notify players about new game requests and accepted requests; expire old ones."""
    if not bot:
        return
    webapp_url = (os.getenv("WEBAPP_URL") or "").strip().rstrip("/")
    try:
        client = _get_client()

        # Expire old requests
        now_iso = datetime.now(timezone.utc).isoformat()
        client.table("game_requests").update({"status": "expired"}).eq("status", "active").lt("expires_at", now_iso).execute()

        # Notify about new active requests (notification_sent_at IS NULL)
        active_r = (
            client.table("game_requests")
            .select("id, player_id, type, division_id")
            .eq("status", "active")
            .is_("notification_sent_at", "null")
            .execute()
        )
        for req in active_r.data or []:
            author_r = client.table("players").select("name").eq("id", req["player_id"]).execute()
            author_name = (author_r.data or [{}])[0].get("name", "Игрок") if author_r.data else "Игрок"

            if req["type"] == "division" and req.get("division_id"):
                dp_r = (
                    client.table("division_players")
                    .select("player_id")
                    .eq("division_id", req["division_id"])
                    .execute()
                )
                target_player_ids = [
                    dp["player_id"] for dp in (dp_r.data or [])
                    if dp["player_id"] != req["player_id"]
                ]
            else:
                all_r = client.table("players").select("id").eq("is_active", True).execute()
                target_player_ids = [
                    p["id"] for p in (all_r.data or [])
                    if p["id"] != req["player_id"]
                ]

            game_type_label = "игру лиги" if req["type"] == "division" else "дружескую игру"
            text = f"🏓 {author_name} ищет {game_type_label}!"
            if webapp_url:
                text += f"\n\nОткройте приложение, чтобы откликнуться."

            for pid in target_player_ids:
                tg_r = client.table("players").select("telegram_id").eq("id", pid).execute()
                if not tg_r.data or tg_r.data[0].get("telegram_id") is None:
                    continue
                tg_id = int(tg_r.data[0]["telegram_id"])
                try:
                    if webapp_url:
                        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                        kb = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="Открыть приложение", url=webapp_url)],
                        ])
                        await bot.send_message(tg_id, text, reply_markup=kb)
                    else:
                        await bot.send_message(tg_id, text)
                except Exception as e:
                    logger.warning("Failed to send game_request notification to %s: %s", tg_id, e)

            client.table("game_requests").update(
                {"notification_sent_at": now_iso}
            ).eq("id", req["id"]).execute()

        # Notify about accepted requests
        accepted_r = (
            client.table("game_requests")
            .select("id, player_id, accepted_by")
            .eq("status", "accepted")
            .eq("accepted_notification_sent", False)
            .execute()
        )
        for req in accepted_r.data or []:
            author_r = client.table("players").select("name, telegram_id, telegram_username").eq("id", req["player_id"]).execute()
            acceptor_r = client.table("players").select("name, telegram_id, telegram_username").eq("id", req["accepted_by"]).execute()
            author = (author_r.data or [{}])[0] if author_r.data else {}
            acceptor = (acceptor_r.data or [{}])[0] if acceptor_r.data else {}

            if author.get("telegram_id"):
                contact = f"@{acceptor.get('telegram_username')}" if acceptor.get("telegram_username") else acceptor.get("name", "Игрок")
                try:
                    await bot.send_message(
                        int(author["telegram_id"]),
                        f"🏓 {acceptor.get('name', 'Игрок')} готов сыграть с вами! Свяжитесь: {contact}"
                    )
                except Exception as e:
                    logger.warning("Failed to notify author %s: %s", author.get("telegram_id"), e)

            if acceptor.get("telegram_id"):
                contact = f"@{author.get('telegram_username')}" if author.get("telegram_username") else author.get("name", "Игрок")
                try:
                    await bot.send_message(
                        int(acceptor["telegram_id"]),
                        f"🏓 Вы откликнулись на игру с {author.get('name', 'Игрок')}! Свяжитесь: {contact}"
                    )
                except Exception as e:
                    logger.warning("Failed to notify acceptor %s: %s", acceptor.get("telegram_id"), e)

            client.table("game_requests").update(
                {"accepted_notification_sent": True}
            ).eq("id", req["id"]).execute()

    except Exception as e:
        logger.exception("_send_game_request_notifications failed: %s", e)


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
    _scheduler.add_job(
        _send_pending_confirm_notifications,
        CronTrigger(minute="*/2"),
        args=[bot],
        id="pending_confirm_notify",
    )
    _scheduler.add_job(
        _send_game_request_notifications,
        CronTrigger(minute="*/2"),
        args=[bot],
        id="game_request_notify",
    )
    _scheduler.start()
    logger.info("Scheduler started (daily 23:55, pending_confirm every 2 min, game_requests every 2 min)")
