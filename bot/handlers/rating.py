"""
Обработчики просмотра рейтинга. Топ-20, текущий игрок выделен.
"""
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from services.supabase_client import get_rating_top, get_player_by_telegram_id

router = Router()


async def _send_rating(message_or_chat, telegram_id: int):
    """Отправить топ-20 рейтинга в чат; выделить игрока с telegram_id."""
    try:
        top = get_rating_top(limit=20)
    except Exception:
        await message_or_chat.answer("Рейтинг временно недоступен. Попробуйте позже.")
        return
    if not top:
        await message_or_chat.answer("Рейтинг пока пуст.")
        return
    current = get_player_by_telegram_id(telegram_id)
    current_id = current["id"] if current else None
    lines = ["🏆 <b>Рейтинг (топ-20)</b>\n"]
    for i, row in enumerate(top, 1):
        name = row.get("name", "—")
        rating_val = row.get("rating", 0)
        r_str = f"{i}. {name} — {rating_val:.2f}"
        if row.get("id") == current_id:
            r_str = f"▶ {r_str} ◀"
        lines.append(r_str)
    await message_or_chat.answer("\n".join(lines))


@router.message(Command("rating"))
async def cmd_rating(message: Message) -> None:
    await _send_rating(message, message.from_user.id)
