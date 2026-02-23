"""
Расчёт изменения рейтинга по формулам ФНТР.

КС (коэф. счёта): 3:0 или 0:3 → 1.2, 3:1 или 1:3 → 1.0, 3:2 или 2:3 → 0.8
КД передаётся как параметр.

ПРв = (100 – (РТВ – РТП)) / 10 * КД * КС   (победитель)
ПРп = -(100 – (РТВ – РТП)) / 20 * КД * КС   (проигравший)
"""
from decimal import Decimal
from typing import Tuple


def calculate_score_coef(sets_p1: int, sets_p2: int) -> float:
    """
    КС по счёту сетов (любой порядок).
    ​3:0 или 0:3 → 1.2, 3:1 или 1:3 → 1.0, 3:2 или 2:3 → 0.8
    """
    a, b = sets_p1, sets_p2
    if (a == 3 and b == 0) or (a == 0 and b == 3):
        return 1.2
    if (a == 3 and b == 1) or (a == 1 and b == 3):
        return 1.0
    if (a == 3 and b == 2) or (a == 2 and b == 3):
        return 0.8
    return 1.0


def calculate_match_rating(
    winner_rating: float,
    loser_rating: float,
    winner_sets: int,
    loser_sets: int,
    kd: float,
) -> Tuple[float, float]:
    """
    Изменение рейтинга за матч.
    winner_rating, loser_rating — рейтинги до матча;
    winner_sets, loser_sets — сеты победителя и проигравшего;
    kd — коэффициент дивизиона (КД).
    Возвращает (delta_winner, delta_loser).
    """
    rw = Decimal(str(winner_rating))
    rl = Decimal(str(loser_rating))
    kd_dec = Decimal(str(kd))
    ks = Decimal(str(calculate_score_coef(winner_sets, loser_sets)))

    diff = rw - rl
    base = (Decimal("100") - diff) / Decimal("10")
    delta_winner = (base * kd_dec * ks).quantize(Decimal("0.01"))
    delta_loser = -(base / Decimal("2") * kd_dec * ks).quantize(Decimal("0.01"))

    return (float(delta_winner), float(delta_loser))


# Обратная совместимость со старыми именами
def get_score_coef(sets_winner: int, sets_loser: int) -> Decimal:
    return Decimal(str(calculate_score_coef(sets_winner, sets_loser)))


def calc_rating_delta(
    rating_winner: float,
    rating_loser: float,
    division_coef: float,
    sets_winner: int,
    sets_loser: int,
) -> Tuple[float, float]:
    return calculate_match_rating(
        rating_winner, rating_loser, sets_winner, sets_loser, division_coef
    )
