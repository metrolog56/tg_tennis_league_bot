"""
Inline-клавиатуры бота.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню: Мой дивизион, Рейтинг, Регламент, Внести результат."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🏓 Мой дивизион", callback_data="menu:division"),
        InlineKeyboardButton(text="📊 Рейтинг", callback_data="menu:rating"),
    )
    builder.row(
        InlineKeyboardButton(text="📋 Регламент", callback_data="menu:rules"),
        InlineKeyboardButton(text="➕ Внести результат", callback_data="menu:result"),
    )
    return builder.as_markup()


def get_opponents_keyboard(division_players: list, current_player_id: str):
    """Кнопки выбора соперника (исключая текущего игрока)."""
    builder = InlineKeyboardBuilder()
    for dp in division_players:
        player = dp.get("player") or dp
        pid = player.get("id") if isinstance(player, dict) else getattr(player, "id", None)
        name = player.get("name", "—") if isinstance(player, dict) else getattr(player, "name", "—")
        if str(pid) == str(current_player_id):
            continue
        builder.row(
            InlineKeyboardButton(text=name, callback_data=f"result:opp:{pid}")
        )
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="result:cancel"))
    return builder.as_markup()


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Да / Нет для подтверждения результата."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data="result:confirm:yes"),
        InlineKeyboardButton(text="❌ Нет", callback_data="result:confirm:no"),
    )
    return builder.as_markup()
