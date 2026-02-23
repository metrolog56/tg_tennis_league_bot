"""
Команды администратора. Доступ только при is_admin или ADMIN_TELEGRAM_ID.
"""
import os
from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

from services.supabase_client import (
    _get_client,
    get_player_by_telegram_id,
    get_active_season,
)

router = Router()

MONTH_NAMES = [
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]


def is_admin(telegram_id: int) -> bool:
    """Проверка: ADMIN_TELEGRAM_ID или is_admin в БД."""
    admin_id = os.getenv("ADMIN_TELEGRAM_ID")
    if admin_id and str(telegram_id) == str(admin_id.strip()):
        return True
    try:
        player = get_player_by_telegram_id(telegram_id)
        return bool(player and player.get("is_admin"))
    except Exception:
        return False


async def _admin_only(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа.")
        return False
    return True


@router.message(Command("addplayer"), F.text)
async def cmd_addplayer(message: Message, command: CommandObject) -> None:
    """Добавить игрока: бот отвечает ссылкой для регистрации."""
    if not await _admin_only(message):
        return
    name = command.args and command.args.strip()
    if not name:
        await message.answer("Использование: /addplayer <имя>, например: /addplayer Иван Иванов")
        return
    bot_info = await message.bot.get_me()
    bot_username = bot_info.username
    link = f"https://t.me/{bot_username}"
    await message.answer(
        f"Игрок <b>{name}</b> может зарегистрироваться, перейдя по ссылке и нажав /start:\n\n{link}\n\n"
        "После регистрации назначьте его в дивизион: /assignplayer <номер_дивизиона> @username"
    )


@router.message(Command("newseason"))
async def cmd_newseason(message: Message) -> None:
    """Создать новый сезон (тур) для текущего месяца."""
    if not await _admin_only(message):
        return
    now = datetime.now(timezone.utc)
    year, month = now.year, now.month
    name = f"{MONTH_NAMES[month]} {year}"
    try:
        client = _get_client()
        r = client.table("seasons").insert({
            "year": year,
            "month": month,
            "name": name,
            "status": "active",
        }).select().execute()
        if r.data and len(r.data) > 0:
            await message.answer(f"Сезон создан: <b>{name}</b> (id: {r.data[0]['id']})")
        else:
            await message.answer("Не удалось создать сезон (возможно, такой месяц уже есть).")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@router.message(Command("adddivision"), F.text)
async def cmd_adddivision(message: Message, command: CommandObject) -> None:
    """Создать дивизион в текущем сезоне. Использование: /adddivision <номер>"""
    if not await _admin_only(message):
        return
    args = (command.args or "").strip()
    if not args:
        await message.answer("Использование: /adddivision <номер>, например: /adddivision 1")
        return
    try:
        num = int(args)
    except ValueError:
        await message.answer("Номер дивизиона должен быть числом.")
        return
    # КД по умолчанию: 1=0.30, 2=0.27, 3=0.25, 4=0.22
    coefs = {1: 0.30, 2: 0.27, 3: 0.25, 4: 0.22}
    coef = coefs.get(num, 0.22)
    season = get_active_season()
    if not season:
        await message.answer("Нет активного сезона. Создайте его: /newseason")
        return
    try:
        client = _get_client()
        r = client.table("divisions").insert({
            "season_id": season["id"],
            "number": num,
            "coef": coef,
        }).select().execute()
        if r.data and len(r.data) > 0:
            await message.answer(f"Дивизион №{num} создан в сезоне {season.get('name', '')}.")
        else:
            await message.answer("Не удалось создать дивизион (возможно, такой номер уже есть).")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@router.message(Command("assignplayer"), F.text)
async def cmd_assignplayer(message: Message, command: CommandObject) -> None:
    """Назначить игрока в дивизион. Использование: /assignplayer <номер_дивизиона> @username"""
    if not await _admin_only(message):
        return
    args = (command.args or "").strip()
    parts = args.split()
    if len(parts) < 2:
        await message.answer(
            "Использование: /assignplayer <номер_дивизиона> @username\n"
            "Пример: /assignplayer 1 @ivanov"
        )
        return
    try:
        div_num = int(parts[0])
    except ValueError:
        await message.answer("Номер дивизиона должен быть числом.")
        return
    username = parts[1].lstrip("@")
    season = get_active_season()
    if not season:
        await message.answer("Нет активного сезона.")
        return
    client = _get_client()
    div_r = (
        client.table("divisions")
        .select("id")
        .eq("season_id", season["id"])
        .eq("number", div_num)
        .execute()
    )
    if not div_r.data or len(div_r.data) == 0:
        await message.answer(f"Дивизион №{div_num} не найден в текущем сезоне.")
        return
    division_id = div_r.data[0]["id"]
    pl_r = (
        client.table("players")
        .select("id, name")
        .eq("telegram_username", username)
        .execute()
    )
    if not pl_r.data or len(pl_r.data) == 0:
        await message.answer(f"Игрок с username @{username} не найден. Он должен сначала нажать /start.")
        return
    player_id = pl_r.data[0]["id"]
    player_name = pl_r.data[0].get("name", "—")
    try:
        client.table("division_players").insert({
            "division_id": division_id,
            "player_id": player_id,
        }).execute()
        await message.answer(f"Игрок <b>{player_name}</b> (@{username}) назначен в дивизион №{div_num}.")
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            await message.answer(f"Игрок уже в этом дивизионе.")
        else:
            await message.answer(f"Ошибка: {e}")


@router.message(Command("closetour"))
async def cmd_closetour(message: Message) -> None:
    """Закрыть тур: несыгранные матчи 0-0, рассчитать итоги, закрыть сезон."""
    if not await _admin_only(message):
        return
    try:
        client = _get_client()
        season = get_active_season()
        if not season:
            await message.answer("Нет активного сезона.")
            return
        season_id = season["id"]
        divs = client.table("divisions").select("id").eq("season_id", season_id).execute()
        if not divs.data:
            await message.answer("В сезоне нет дивизионов.")
            return
        for d in divs.data:
            div_id = d["id"]
            # Все pending матчи → not_played, 0-0
            client.table("matches").update({
                "status": "not_played",
                "sets_player1": 0,
                "sets_player2": 0,
            }).eq("division_id", div_id).eq("status", "pending").execute()
            # Позиции в дивизионе по total_points, затем по разнице сетов
            dps = (
                client.table("division_players")
                .select("id, total_points, total_sets_won, total_sets_lost")
                .eq("division_id", div_id)
                .execute()
            )
            if not dps.data:
                continue
            rows = dps.data
            def key(r):
                pts = r.get("total_points") or 0
                sw = r.get("total_sets_won") or 0
                sl = r.get("total_sets_lost") or 0
                return (pts, sw - sl)
            for pos, row in enumerate(sorted(rows, key=key, reverse=True), 1):
                client.table("division_players").update({"position": pos}).eq("id", row["id"]).execute()
        client.table("seasons").update({"status": "closed"}).eq("id", season_id).execute()
        await message.answer(f"Тур закрыт. Сезон «{season.get('name', '')}» переведён в статус closed.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
