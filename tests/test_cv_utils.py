"""Tests for computer vision utilities."""

import numpy as np
from cv_utils import group_shots


def test_group_shots_empty():
    result = group_shots([])
    assert result == []


def test_group_shots_single():
    result = group_shots([(100, 100)])
    assert len(result) == 1
    assert result[0] == [(100, 100)]


def test_group_shots_close_together():
    shots = [(100, 100), (110, 110), (105, 95)]
    result = group_shots(shots, dist_threshold_px=50)
    assert len(result) == 1
    assert len(result[0]) == 3


def test_group_shots_two_groups():
    shots = [(100, 100), (110, 110), (500, 500), (510, 510)]
    result = group_shots(shots, dist_threshold_px=50)
    assert len(result) == 2


def test_group_shots_each_isolated():
    shots = [(0, 0), (1000, 1000), (2000, 2000)]
    result = group_shots(shots, dist_threshold_px=50)
    assert len(result) == 3
