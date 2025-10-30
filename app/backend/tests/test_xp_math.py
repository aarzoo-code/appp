import pytest

from backend import schemas


def test_xp_for_level_monotonic():
    # thresholds should increase with level
    prev = 0
    for lvl in range(1, 11):
        t = schemas.xp_for_level(lvl)
        assert t > prev
        prev = t


def test_compute_new_level_boundaries():
    # ensure compute_new_level maps XP to the correct level boundaries
    assert schemas.compute_new_level(0) == 1
    # xp just below level 2 threshold
    t2 = schemas.xp_for_level(2)
    assert schemas.compute_new_level(t2 - 1) == 1
    assert schemas.compute_new_level(t2) >= 2


def test_next_level_threshold_consistent():
    for lvl in range(1, 6):
        assert schemas.next_level_threshold(lvl) == schemas.xp_for_level(lvl + 1)
