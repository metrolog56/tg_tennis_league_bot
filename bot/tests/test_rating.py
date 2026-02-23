"""
Unit-тесты расчёта рейтинга ФНТР.
"""
import pytest
from services.rating_calculator import (
    calculate_score_coef,
    calculate_match_rating,
)


class TestCalculateScoreCoef:
    """КС: 3:0/0:3 → 1.2, 3:1/1:3 → 1.0, 3:2/2:3 → 0.8"""

    def test_3_0(self):
        assert calculate_score_coef(3, 0) == 1.2
        assert calculate_score_coef(0, 3) == 1.2

    def test_3_1(self):
        assert calculate_score_coef(3, 1) == 1.0
        assert calculate_score_coef(1, 3) == 1.0

    def test_3_2(self):
        assert calculate_score_coef(3, 2) == 0.8
        assert calculate_score_coef(2, 3) == 0.8

    def test_other_returns_1_0(self):
        assert calculate_score_coef(2, 2) == 1.0
        assert calculate_score_coef(1, 0) == 1.0


class TestCalculateMatchRating:
    """ПРв = (100 – (РТВ – РТП)) / 10 * КД * КС, ПРп = -.../ 20 * КД * КС"""

    def test_winner_positive_loser_negative(self):
        d_w, d_l = calculate_match_rating(100.0, 100.0, 3, 0, 0.30)
        assert d_w > 0
        assert d_l < 0

    def test_equal_rating_3_0_kd_30(self):
        # 100 - 100 = 0, base = 10, winner = 10 * 0.30 * 1.2 = 3.6, loser = -1.8
        d_w, d_l = calculate_match_rating(100.0, 100.0, 3, 0, 0.30)
        assert d_w == pytest.approx(3.6, abs=0.01)
        assert d_l == pytest.approx(-1.8, abs=0.01)

    def test_equal_rating_3_1_kd_30(self):
        # base = 10, winner = 10 * 0.30 * 1.0 = 3.0, loser = -1.5
        d_w, d_l = calculate_match_rating(100.0, 100.0, 3, 1, 0.30)
        assert d_w == pytest.approx(3.0, abs=0.01)
        assert d_l == pytest.approx(-1.5, abs=0.01)

    def test_equal_rating_3_2_kd_30(self):
        # base = 10, winner = 10 * 0.30 * 0.8 = 2.4, loser = -1.2
        d_w, d_l = calculate_match_rating(100.0, 100.0, 3, 2, 0.30)
        assert d_w == pytest.approx(2.4, abs=0.01)
        assert d_l == pytest.approx(-1.2, abs=0.01)

    def test_underdog_wins_more_points(self):
        # Победитель с рейтингом ниже получает больше очков
        d_low_wins, _ = calculate_match_rating(90.0, 110.0, 3, 1, 0.30)
        d_high_wins, _ = calculate_match_rating(110.0, 90.0, 3, 1, 0.30)
        assert d_low_wins > d_high_wins

    def test_kd_affects_delta(self):
        d1_w, _ = calculate_match_rating(100.0, 100.0, 3, 0, 0.30)
        d2_w, _ = calculate_match_rating(100.0, 100.0, 3, 0, 0.22)
        assert d1_w > d2_w
