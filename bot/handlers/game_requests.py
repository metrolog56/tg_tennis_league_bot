"""
Game request handlers: callbacks for accepting/declining division challenges,
and notification helpers called by the notify server.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from services.supabase_client import get_player_by_telegram_id

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)

router = Router()


def _get_client():
    from services.supabase_client import _get_client as get
    return get()


# ---------------------------------------------------------------------------
# Telegram callback handlers (inline buttons on challenge notifications)
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("gamereq:accept:"))
async def gamereq_accept(callback: CallbackQuery) -> None:
    request_id = callback.data.replace("gamereq:accept:", "").strip()
    telegram_id = callback.from_user.id

    player = get_player_by_telegram_id(telegram_id)
    if not player:
        await callback.answer("Игрок не найден.", show_alert=True)
        return

    client = _get_client()
    r = client.table("game_requests").select("*").eq("id", request_id).execute()
    if not r.data:
        await callback.answer("Запрос не найден.", show_alert=True)
        return
    req = r.data[0]

    if req["status"] != "pending":
        await callback.answer("Запрос уже неактивен.", show_alert=True)
        return

    if req.get("type") == "division_challenge":
        if req.get("target_player_id") != player["id"]:
            await callback.answer("Этот вызов не адресован вам.", show_alert=True)
            return
    elif req["requester_id"] == player["id"]:
        await callback.answer("Нельзя принять собственный запрос.", show_alert=True)
        return

    upd = (
        client.table("game_requests")
        .update({"status": "accepted", "accepted_by_id": player["id"]})
        .eq("id", request_id)
        .eq("status", "pending")
        .select()
        .execute()
    )
    if not upd.data:
        await callback.answer("Запрос уже был принят другим игроком.", show_alert=True)
        return

    await callback.answer("Принято! 🤝", show_alert=False)
    try:
        await callback.message.edit_text(
            "✅ Вы приняли запрос на игру! 🤝\n"
            "Договоритесь с соперником об удобном времени."
        )
    except Exception:
        pass

    await send_game_request_accepted_notify(request_id, callback.bot)


@router.callback_query(F.data.startswith("gamereq:decline:"))
async def gamereq_decline(callback: CallbackQuery) -> None:
    request_id = callback.data.replace("gamereq:decline:", "").strip()
    telegram_id = callback.from_user.id

    player = get_player_by_telegram_id(telegram_id)
    if not player:
        await callback.answer("Игрок не найден.", show_alert=True)
        return

    client = _get_client()
    r = (
        client.table("game_requests")
        .select("id, requester_id, target_player_id, status, type")
        .eq("id", request_id)
        .execute()
    )
    if not r.data:
        await callback.answer("Запрос не найден.", show_alert=True)
        return
    req = r.data[0]

    if req["status"] != "pending":
        await callback.answer("Запрос уже неактивен.", show_alert=True)
        return

    if req.get("type") == "division_challenge" and req.get("target_player_id") != player["id"]:
        await callback.answer("Этот вызов не адресован вам.", show_alert=True)
        return

    client.table("game_requests").update({"status": "cancelled"}).eq("id", request_id).eq("status", "pending").execute()

    await callback.answer("Отклонено.", show_alert=False)
    try:
        await callback.message.edit_text("Вы отклонили запрос на игру.")
    except Exception:
        pass

    # Notify requester about the decline
    requester_r = (
        client.table("players")
        .select("telegram_id, name")
        .eq("id", req["requester_id"])
        .execute()
    )
    if requester_r.data and requester_r.data[0].get("telegram_id"):
        decliner_name = player.get("name", "Игрок")
        try:
            await callback.bot.send_message(
                int(requester_r.data[0]["telegram_id"]),
                f"<b>{decliner_name}</b> отклонил ваш запрос на матч.",
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Notification helpers (called by notify_server.py)
# ---------------------------------------------------------------------------

async def send_game_request_notify(request_id: str, bot: Optional["Bot"]) -> bool:
    """Send a division challenge notification to the target player."""
    if not bot:
        return False
    webapp_url = (os.getenv("WEBAPP_URL") or "").strip().rstrip("/")
    try:
        client = _get_client()
        r = (
            client.table("game_requests")
            .select("requester_id, target_player_id, status, notification_sent_at")
            .eq("id", request_id)
            .execute()
        )
        if not r.data:
            return False
        req = r.data[0]
        if req.get("status") != "pending":
            return True
        if req.get("notification_sent_at"):
            return True

        target_id = req.get("target_player_id")
        if not target_id:
            return False

        players_r = (
            client.table("players")
            .select("id, name, telegram_id")
            .in_("id", [req["requester_id"], target_id])
            .execute()
        )
        by_id = {p["id"]: p for p in (players_r.data or [])}
        requester = by_id.get(req["requester_id"], {})
        target = by_id.get(target_id, {})

        telegram_id = target.get("telegram_id")
        if not telegram_id:
            return False

        requester_name = requester.get("name", "Игрок")
        text = (
            f"🎾 <b>{requester_name}</b> вызывает тебя на матч лиги!\n"
            "Прими или отклони вызов."
        )
        buttons: list[list[InlineKeyboardButton]] = [
            [
                InlineKeyboardButton(text="Принять 🤝", callback_data=f"gamereq:accept:{request_id}"),
                InlineKeyboardButton(text="Отклонить", callback_data=f"gamereq:decline:{request_id}"),
            ],
        ]
        if webapp_url:
            buttons.append([InlineKeyboardButton(text="Открыть приложение", url=webapp_url)])

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await bot.send_message(int(telegram_id), text, reply_markup=kb)

        now_iso = datetime.now(timezone.utc).isoformat()
        client.table("game_requests").update({"notification_sent_at": now_iso}).eq("id", request_id).execute()
        logger.info("Sent game request notify for %s to player %s", request_id, target_id)
        return True
    except Exception as e:
        logger.exception("send_game_request_notify failed for %s: %s", request_id, e)
        return False


async def send_game_request_accepted_notify(request_id: str, bot: Optional["Bot"]) -> bool:
    """Notify both players that a game request was accepted."""
    if not bot:
        return False
    try:
        client = _get_client()
        r = (
            client.table("game_requests")
            .select("requester_id, accepted_by_id, status")
            .eq("id", request_id)
            .execute()
        )
        if not r.data:
            return False
        req = r.data[0]
        if req.get("status") != "accepted":
            return False

        requester_id = req.get("requester_id")
        acceptor_id = req.get("accepted_by_id")
        if not requester_id or not acceptor_id:
            return False

        ids = list({requester_id, acceptor_id})
        players_r = client.table("players").select("id, name, telegram_id").in_("id", ids).execute()
        by_id = {p["id"]: p for p in (players_r.data or [])}

        requester = by_id.get(requester_id, {})
        acceptor = by_id.get(acceptor_id, {})
        requester_name = requester.get("name", "Игрок")
        acceptor_name = acceptor.get("name", "Игрок")

        requester_tid = requester.get("telegram_id")
        if requester_tid:
            try:
                await bot.send_message(
                    int(requester_tid),
                    f"🎾 <b>{acceptor_name}</b> принял(а) ваш запрос на игру! 🤝\n"
                    "Договоритесь об удобном времени.",
                )
            except Exception:
                pass

        acceptor_tid = acceptor.get("telegram_id")
        if acceptor_tid and acceptor_tid != requester_tid:
            try:
                await bot.send_message(
                    int(acceptor_tid),
                    f"🎾 Отлично! Вы договорились с <b>{requester_name}</b> о матче! 🤝\n"
                    "Удачной игры!",
                )
            except Exception:
                pass

        logger.info("Sent game_request_accepted notify for %s", request_id)
        return True
    except Exception as e:
        logger.exception("send_game_request_accepted_notify failed for %s: %s", request_id, e)
        return False


async def send_open_game_request_notify(request_id: str, bot: Optional["Bot"]) -> bool:
    """Broadcast open game request (open_league/open_casual) to all players with telegram_id except requester."""
    if not bot:
        return False
    webapp_url = (os.getenv("WEBAPP_URL") or "").strip().rstrip("/")
    try:
        client = _get_client()
        r = (
            client.table("game_requests")
            .select("requester_id, type, status, notification_sent_at")
            .eq("id", request_id)
            .execute()
        )
        if not r.data:
            return False
        req = r.data[0]
        if req.get("status") != "pending":
            return True
        if req.get("notification_sent_at"):
            return True
        if req.get("type") not in ("open_league", "open_casual"):
            return False

        requester_id = req.get("requester_id")
        if not requester_id:
            return False

        players_r = (
            client.table("players")
            .select("id, name, telegram_id")
            .neq("id", requester_id)
            .not_.is_("telegram_id", "null")
            .execute()
        )
        players = players_r.data or []
        if not players:
            return False

        # Map requester for name, fall back to first match in players list if missing
        requester = next((p for p in players if p["id"] == requester_id), None)
        if not requester:
            # fetch explicitly if not in list
            r_req = (
                client.table("players")
                .select("id, name, telegram_id")
                .eq("id", requester_id)
                .execute()
            )
            requester = (r_req.data or [{}])[0]

        author_name = requester.get("name", "Игрок")
        is_casual = req.get("type") == "open_casual"
        game_label = "Просто поиграть" if is_casual else "Матч лиги"

        text = (
            f"🎾 <b>{author_name}</b> ищет соперника ({game_label}).\n"
            "Откройте мини‑приложение или нажмите кнопку, чтобы откликнуться."
        )

        buttons: list[list[InlineKeyboardButton]] = [
            [InlineKeyboardButton(text="Откликнуться 🤝", callback_data=f"gamereq:accept:{request_id}")],
        ]
        if webapp_url:
            buttons.append([InlineKeyboardButton(text="Открыть приложение", url=webapp_url)])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        sent_any = False
        for p in players:
            tid = p.get("telegram_id")
            if not tid:
                continue
            try:
                await bot.send_message(int(tid), text, reply_markup=kb)
                sent_any = True
            except Exception:
                continue

        if sent_any:
            now_iso = datetime.now(timezone.utc).isoformat()
            client.table("game_requests").update({"notification_sent_at": now_iso}).eq("id", request_id).execute()
            logger.info("Sent open game request notify for %s", request_id)
        return sent_any
    except Exception as e:
        logger.exception("send_open_game_request_notify failed for %s: %s", request_id, e)
        return False
