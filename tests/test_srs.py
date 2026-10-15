import pytest

from cornerstone.srs import MIN_EF, sm2


def test_first_three_correct_reviews_follow_1_6_then_interval_times_ef():
    ef, iv, reps = sm2(2.5, 0, 0, 4)
    assert (iv, reps) == (1, 1) and ef == pytest.approx(2.5)        # grade 4 leaves ef unchanged
    ef, iv, reps = sm2(ef, iv, reps, 4)
    assert (iv, reps) == (6, 2)
    ef, iv, reps = sm2(ef, iv, reps, 4)
    assert (iv, reps) == (15, 3)                                    # round(6 * 2.5)


def test_ef_change_per_grade():
    assert sm2(2.5, 0, 0, 5)[0] == pytest.approx(2.6)
    assert sm2(2.5, 0, 0, 3)[0] == pytest.approx(2.36)
    assert sm2(2.5, 0, 0, 0)[0] == pytest.approx(1.7)


def test_failure_resets_reps_and_interval_but_lowers_ef():
    ef, iv, reps = sm2(2.5, 15, 3, 2)
    assert (iv, reps) == (1, 0) and ef == pytest.approx(2.18)


def test_ef_never_below_floor():
    ef = 1.4
    for _ in range(5):
        ef, _, _ = sm2(ef, 1, 0, 0)
    assert ef == MIN_EF


def test_bad_grade():
    for g in (-1, 6, 7):
        with pytest.raises(ValueError):
            sm2(2.5, 0, 0, g)
