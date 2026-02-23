"""
Unit-тесты расчёта рейтинга ФНТР.
"""
import pytest
from services.rating_calculator import (
    calculate_score_coef,
    calculate_match_rating,
)


class TestCalculateKc:
    """КС: все 6 допустимых счётов — 3:0→1.2, 3:1→1.0, 3:2→0.8 и обратные."""

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
    """ПРв и ПРп по формулам ФНТР."""

    def test_winner_positive_loser_negative(self):
        d_w, d_l = calculate_match_rating(100.0, 100.0, 3, 0, 0.30)
        assert d_w > 0
        assert d_l < 0

    def test_equal_rating_3_0_kd_30(self):
        d_w, d_l = calculate_match_rating(100.0, 100.0, 3, 0, 0.30)
        assert d_w == pytest.approx(3.6, abs=0.01)
        assert d_l == pytest.approx(-1.8, abs=0.01)

    def test_equal_rating_3_1_kd_30(self):
        d_w, d_l = calculate_match_rating(100.0, 100.0, 3, 1, 0.30)
        assert d_w == pytest.approx(3.0, abs=0.01)
        assert d_l == pytest.approx(-1.5, abs=0.01)

    def test_equal_rating_3_2_kd_30(self):
        d_w, d_l = calculate_match_rating(100.0, 100.0, 3, 2, 0.30)
        assert d_w == pytest.approx(2.4, abs=0.01)
        assert d_l == pytest.approx(-1.2, abs=0.01)

    def test_winner_gains_more(self):
        """Победитель с меньшим рейтингом получает больше очков."""
        d_low_wins, _ = calculate_match_rating(90.0, 110.0, 3, 1, 0.30)
        d_high_wins, _ = calculate_match_rating(110.0, 90.0, 3, 1, 0.30)
        assert d_low_wins > d_high_wins

    def test_loser_lower_rating_loses_less(self):
        """Более слабый при проигрыше теряет меньше (меньше по модулю)."""
        _, d_weak_loses = calculate_match_rating(110.0, 90.0, 3, 1, 0.30)   # слабый 90 проиграл
        _, d_strong_loses = calculate_match_rating(90.0, 110.0, 3, 1, 0.30)  # сильный 110 проиграл
        assert abs(d_weak_loses) < abs(d_strong_loses)

    def test_not_played_gives_zero(self):
        """Несыгранный матч (0:0) даёт изменение рейтинга 0."""
        d_w, d_l = calculate_match_rating(100.0, 100.0, 0, 0, 0.30)
        assert d_w == 0.0
        assert d_l == 0.0

    def test_result_3_0_vs_3_2(self):
        """При одинаковых рейтингах счёт 3:0 даёт больше очков победителю, чем 3:2."""
        d_30_w, _ = calculate_match_rating(100.0, 100.0, 3, 0, 0.30)
        d_32_w, _ = calculate_match_rating(100.0, 100.0, 3, 2, 0.30)
        assert d_30_w > d_32_w
        assert d_30_w == pytest.approx(3.6, abs=0.01)
        assert d_32_w == pytest.approx(2.4, abs=0.01)

    def test_kd_affects_delta(self):
        d1_w, _ = calculate_match_rating(100.0, 100.0, 3, 0, 0.30)
        d2_w, _ = calculate_match_rating(100.0, 100.0, 3, 0, 0.22)
        assert d1_w > d2_w
