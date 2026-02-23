"""
Обработчики общих команд: /start, /help.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from services.supabase_client import get_player_by_telegram_id, create_player, get_player_division
from keyboards.inline import get_main_menu_keyboard

router = Router()


def _get_name_from_user(message: Message) -> str:
    """Имя из профиля Telegram."""
    user = message.from_user
    if user.first_name or user.last_name:
        return " ".join(filter(None, [user.first_name, user.last_name or ""])).strip()
    return user.username or f"User_{user.id}"


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Регистрация по telegram_id при необходимости, приветствие с кнопками."""
    telegram_id = message.from_user.id
    username = message.from_user.username
    name = _get_name_from_user(message)

    try:
        player = get_player_by_telegram_id(telegram_id)
        if not player:
            player = create_player(
                telegram_id=telegram_id,
                name=name,
                telegram_username=username,
            )
            if not player:
                await message.answer("Ошибка регистрации. Обратитесь к администратору.")
                return
            greet = "Добро пожаловать в лигу! Вы зарегистрированы."
        else:
            greet = "С возвращением!"
    except Exception as e:
        await message.answer(f"Ошибка: {e}. Проверьте настройки бота.")
        return

    text = (
        f"🏓 <b>Лига настольного тенниса</b>\n\n"
        f"{greet}\n\n"
        "Выберите действие:"
    )
    await message.answer(text, reply_markup=get_main_menu_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Список команд."""
    text = (
        "📖 <b>Команды</b>\n\n"
        "/start — главное меню\n"
        "/rating — рейтинг (топ-20)\n"
        "/result — внести результат матча\n"
        "/help — эта справка"
    )
    await message.answer(text)


@router.callback_query(F.data == "menu:rating")
async def menu_rating(callback: CallbackQuery) -> None:
    await callback.answer()
    from handlers.rating import _send_rating
    await _send_rating(callback.message, callback.from_user.id)


@router.callback_query(F.data == "menu:division")
async def menu_division(callback: CallbackQuery) -> None:
    await callback.answer()
    telegram_id = callback.from_user.id
    player = get_player_by_telegram_id(telegram_id)
    if not player:
        await callback.message.answer("Сначала нажмите /start для регистрации.")
        return
    data = get_player_division(player["id"])
    if not data:
        await callback.message.answer("У вас пока нет дивизиона в текущем сезоне. Обратитесь к администратору.")
        return
    div = data["division"]
    season = data.get("season") or {}
    players = data.get("division_players") or []
    lines = [
        f"🏓 <b>Ваш дивизион</b>\n",
        f"Сезон: {season.get('name', '—')}",
        f"Дивизион №{div.get('number', '—')}\n",
        "Участники:",
    ]
    for i, dp in enumerate(sorted(players, key=lambda x: (x.get("position") or 99, x.get("total_points") or 0), reverse=True), 1):
        p = dp.get("player") or dp
        name = p.get("name", "—") if isinstance(p, dict) else getattr(p, "name", "—")
        pts = dp.get("total_points") or 0
        lines.append(f"  {i}. {name} — {pts} очк.")
    await callback.message.answer("\n".join(lines))


@router.callback_query(F.data == "menu:rules")
async def menu_rules(callback: CallbackQuery) -> None:
    await callback.answer()
    text = (
        "📋 <b>Регламент</b>\n\n"
        "• Тур = 1 месяц, в дивизионе все играют друг с другом\n"
        "• Матч: до 3 побед (Best of 5). Допустимые счёты: 3:0, 3:1, 3:2, 2:3, 1:3, 0:3\n"
        "• Очки: победа 2, поражение 1, несыгранный 0\n"
        "• Топ-2 поднимаются в дивизион выше, последние 2 — вниз\n"
        "• Новый игрок: рейтинг 100, последний дивизион\n\n"
        "Рейтинг считается по формулам ФНТР (КД по дивизиону, КС по счёту)."
    )
    await callback.message.answer(text)


@router.callback_query(F.data == "menu:result")
async def menu_result(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "Введите команду /result чтобы внести результат матча пошагово."
    )
