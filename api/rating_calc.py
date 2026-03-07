"""
Rating delta by ФНТР formulas. Mirrors bot/services/rating_calculator.py.
"""
from decimal import Decimal
from typing import Tuple


def _score_coef(sets_winner: int, sets_loser: int) -> float:
    if (sets_winner == 3 and sets_loser == 0) or (sets_winner == 0 and sets_loser == 3):
        return 1.2
    if (sets_winner == 3 and sets_loser == 1) or (sets_winner == 1 and sets_loser == 3):
        return 1.0
    if (sets_winner == 3 and sets_loser == 2) or (sets_winner == 2 and sets_loser == 3):
        return 0.8
    return 1.0


def calculate_match_rating(
    winner_rating: float,
    loser_rating: float,
    winner_sets: int,
    loser_sets: int,
    kd: float,
) -> Tuple[float, float]:
    if winner_sets == 0 and loser_sets == 0:
        return (0.0, 0.0)
    rw = Decimal(str(winner_rating))
    rl = Decimal(str(loser_rating))
    kd_dec = Decimal(str(kd))
    ks = Decimal(str(_score_coef(winner_sets, loser_sets)))
    diff = rw - rl
    base = (Decimal("100") - diff) / Decimal("10")
    delta_winner = float((base * kd_dec * ks).quantize(Decimal("0.01")))
    delta_loser = float(-(base / Decimal("2") * kd_dec * ks).quantize(Decimal("0.01")))
    return (delta_winner, delta_loser)
