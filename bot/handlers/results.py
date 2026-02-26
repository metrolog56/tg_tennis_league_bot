"""
Ввод результата матча: FSM-диалог /result.
"""
from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.supabase_client import (
    get_player_by_telegram_id,
    get_player_division,
    get_existing_match,
    submit_match_result,
)
from keyboards.inline import get_opponents_keyboard, get_confirm_keyboard

router = Router()

VALID_SCORES = [(3, 0), (3, 1), (3, 2), (2, 3), (1, 3), (0, 3)]


class ResultStates(StatesGroup):
    choose_opponent = State()
    enter_score = State()
    confirm = State()


def _parse_score(text: str) -> tuple[int, int] | None:
    """Парсит '3-1', '3:2' и т.п. Возвращает (my_sets, opponent_sets) или None."""
    text = text.strip().replace(":", "-").replace(" ", "")
    if "-" not in text:
        return None
    parts = text.split("-", 1)
    if len(parts) != 2:
        return None
    try:
        a, b = int(parts[0]), int(parts[1])
        if (a, b) in VALID_SCORES:
            return (a, b)
        return None
    except ValueError:
        return None


@router.message(Command("result"))
async def cmd_result(message: Message, state: FSMContext) -> None:
    """Начать ввод результата: показать список соперников."""
    await state.clear()
    telegram_id = message.from_user.id
    player = get_player_by_telegram_id(telegram_id)
    if not player:
        await message.answer("Сначала нажмите /start для регистрации.")
        return
    data = get_player_division(player["id"])
    if not data:
        await message.answer("У вас нет дивизиона в текущем сезоне. Обратитесь к администратору.")
        return
    division = data["division"]
    season = data.get("season") or {}
    players = data.get("division_players") or []
    opponents = [p for p in players if (p.get("player") or p).get("id") != player["id"]]
    if not opponents:
        await message.answer("В дивизионе нет других участников.")
        return
    await state.update_data(
        division_id=division["id"],
        season_id=season.get("id"),
        division_coef=float(division.get("coef", 0.25)),
        my_player_id=player["id"],
    )
    await state.set_state(ResultStates.choose_opponent)
    await message.answer(
        "Выберите соперника:",
        reply_markup=get_opponents_keyboard(players, player["id"]),
    )


@router.callback_query(F.data.startswith("result:opp:"), ResultStates.choose_opponent)
async def result_choose_opponent(callback: CallbackQuery, state: FSMContext) -> None:
    opponent_id = callback.data.replace("result:opp:", "").strip()
    if not opponent_id:
        await callback.answer()
        return
    data = await state.get_data()
    players = get_player_division(data["my_player_id"]).get("division_players") or []
    opponent_name = "Соперник"
    for dp in players:
        p = dp.get("player") or dp
        if str(p.get("id")) == str(opponent_id):
            opponent_name = p.get("name", opponent_name)
            break
    await state.update_data(opponent_id=opponent_id, opponent_name=opponent_name)
    await state.set_state(ResultStates.enter_score)
    await callback.answer()
    await callback.message.edit_text(
        f"Соперник: <b>{opponent_name}</b>\n\n"
        "Введите счёт матча в формате <b>3-1</b> или <b>3-2</b> (ваши сеты — сеты соперника).\n"
        "Допустимые счёты: 3:0, 3:1, 3:2, 2:3, 1:3, 0:3."
    )


@router.message(ResultStates.enter_score, F.text)
async def result_enter_score(message: Message, state: FSMContext) -> None:
    parsed = _parse_score(message.text)
    if parsed is None:
        await message.answer("Неверный формат. Введите счёт, например: 3-1 или 3-2")
        return
    my_sets, opp_sets = parsed
    await state.update_data(my_sets=my_sets, opponent_sets=opp_sets)
    await state.set_state(ResultStates.confirm)
    data = await state.get_data()
    await message.answer(
        f"Вы: <b>{my_sets}</b> сет(а/ов), Соперник ({data.get('opponent_name', '—')}): <b>{opp_sets}</b> сет(а/ов).\nВерно?",
        reply_markup=get_confirm_keyboard(),
    )


@router.callback_query(F.data == "result:confirm:yes", ResultStates.confirm)
async def result_confirm_yes(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    division_id = data["division_id"]
    season_id = data.get("season_id")
    my_id = data["my_player_id"]
    opponent_id = data["opponent_id"]
    my_sets = data["my_sets"]
    opp_sets = data["opponent_sets"]
    coef = data["division_coef"]

    existing = get_existing_match(division_id, my_id, opponent_id)
    if existing and existing.get("status") == "played":
        await state.clear()
        await callback.message.edit_text("Этот матч уже был внесён ранее.")
        return

    match_row, err, deltas = submit_match_result(
        division_id=division_id,
        player1_id=my_id,
        player2_id=opponent_id,
        sets_player1=my_sets,
        sets_player2=opp_sets,
        submitted_by_id=my_id,
        division_coef=coef,
        season_id=season_id or "",
    )
    await state.clear()
    if err:
        await callback.message.edit_text(f"Ошибка: {err}")
        return
    player = get_player_by_telegram_id(callback.from_user.id)
    rating_now = float(player.get("rating", 0)) if player else 0
    my_delta = deltas.get(my_id, 0)
    delta_str = f"+{my_delta:.2f}" if my_delta >= 0 else f"{my_delta:.2f}"
    await callback.message.edit_text(
        f"✅ Результат внесён!\nВаш рейтинг: <b>{rating_now:.2f}</b> ({delta_str})"
    )


@router.callback_query(F.data == "result:confirm:no", ResultStates.confirm)
async def result_confirm_no(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.edit_text("Ввод отменён. Нажмите /result чтобы начать заново.")


@router.callback_query(F.data == "result:cancel")
async def result_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.edit_text("Отменено. Нажмите /result когда будете готовы.")


# Отмена по команде /start или /result
@router.message(ResultStates.enter_score, Command("start"))
@router.message(ResultStates.enter_score, Command("result"))
@router.message(ResultStates.confirm, Command("start"))
@router.message(ResultStates.confirm, Command("result"))
async def result_cancel_cmd(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Ввод результата отменён.")
