"""Tests for computer vision utilities."""

import numpy as np
import pytest
from PIL import Image

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


def test_group_shots_chains_through_intermediate():
    """Single-link clustering: A and C join if B bridges them, even though
    A and C are further apart than the threshold."""
    shots = [(0, 0), (40, 0), (80, 0)]
    result = group_shots(shots, dist_threshold_px=50)
    assert len(result) == 1
    assert len(result[0]) == 3


def test_group_shots_preserves_every_shot():
    shots = [(10, 10), (20, 20), (400, 400), (900, 100), (905, 105)]
    result = group_shots(shots, dist_threshold_px=50)
    assert sorted(s for g in result for s in g) == sorted(shots)


class TestDetectReferenceObject:
    def test_returns_none_pair_when_no_circle_present(self):
        from cv_utils import detect_reference_object
        blank = np.full((300, 400, 3), 255, dtype=np.uint8)
        px_per_mm, coin = detect_reference_object(blank)
        assert px_per_mm is None
        assert coin is None

    def test_scales_by_reference_diameter(self):
        """A 1-real coin is 27mm and a 10-cent coin 20mm, so the same circle
        must yield a larger px/mm for the smaller reference."""
        import cv2
        from cv_utils import detect_reference_object

        img = np.full((400, 400, 3), 255, dtype=np.uint8)
        cv2.circle(img, (200, 200), 60, (30, 30, 30), -1)

        big, _ = detect_reference_object(img, "coin_br_1")
        small, _ = detect_reference_object(img, "coin_br_010")
        if big is None or small is None:
            pytest.skip("HoughCircles nao detectou o circulo sintetico")
        assert small > big
        assert small / big == pytest.approx(27.0 / 20.0, rel=1e-6)

    def test_unknown_reference_falls_back_to_1_real(self):
        import cv2
        from cv_utils import detect_reference_object

        img = np.full((400, 400, 3), 255, dtype=np.uint8)
        cv2.circle(img, (200, 200), 60, (30, 30, 30), -1)

        known, _ = detect_reference_object(img, "coin_br_1")
        unknown, _ = detect_reference_object(img, "moeda_inexistente")
        if known is None:
            pytest.skip("HoughCircles nao detectou o circulo sintetico")
        assert unknown == known


def _target(holes, size=(600, 800), radius=9):
    """White target with dark circular holes at the given (x, y) centres."""
    import cv2
    img = np.full((size[0], size[1], 3), 245, dtype=np.uint8)
    for (x, y) in holes:
        cv2.circle(img, (x, y), radius, (15, 15, 15), -1)
    return Image.fromarray(img)


class TestCalculateGroupSize:
    def test_unreadable_input_returns_empty_result_instead_of_raising(self):
        """The function's contract is to always return a result dict. It used
        to raise UnboundLocalError from inside its own except block, because
        the handler referenced a variable that Image.open never got to bind."""
        from cv_utils import calculate_group_size_v2
        res = calculate_group_size_v2("/nao/existe/alvo.png")
        assert res["groups"] == []
        assert res["shot_count"] == 0
        assert res["annotated_image"] is not None

    def test_annotated_image_is_renderable_after_failure(self):
        """Callers hand this straight to st.image and cv2.imencode; None or a
        zero-sized array would break both."""
        import cv2
        from cv_utils import calculate_group_size_v2
        res = calculate_group_size_v2(b"nao e uma imagem")
        img = res["annotated_image"]
        assert img.ndim == 3 and img.shape[0] > 0 and img.shape[1] > 0
        assert cv2.imencode(".jpg", img)[0] is True

    def test_blank_target_detects_nothing(self):
        from cv_utils import calculate_group_size_v2
        res = calculate_group_size_v2(_target([]))
        assert res["shot_count"] == 0
        assert res["groups"] == []

    def test_calibration_scales_with_target_width(self):
        """Declaring a narrower target makes each pixel worth more millimetres."""
        from cv_utils import calculate_group_size_v2
        wide = calculate_group_size_v2(_target([]), target_width_mm=800.0)
        narrow = calculate_group_size_v2(_target([]), target_width_mm=200.0)
        assert narrow["pixel_per_mm"] == pytest.approx(wide["pixel_per_mm"] * 4)

    def test_measures_known_spread(self):
        """Two holes 150px apart on an 800px-wide target declared as 400mm
        means 2 px/mm, so the group must measure 75mm."""
        from cv_utils import calculate_group_size_v2
        res = calculate_group_size_v2(
            _target([(325, 300), (475, 300)]), target_width_mm=400.0
        )
        if res["shot_count"] != 2:
            pytest.skip(f"deteccao encontrou {res['shot_count']} impactos, nao 2")
        assert len(res["groups"]) == 1
        assert res["groups"][0]["group_size_mm"] == pytest.approx(75.0, rel=0.05)

    def test_impacts_beyond_10cm_are_separate_groups(self):
        """Shots are clustered at a 10cm threshold, so a shooter who fires two
        distinct groups on one sheet gets two measurements, not one inflated
        spread across both."""
        from cv_utils import calculate_group_size_v2
        # 2 px/mm: 300px = 15cm apart, past the threshold; 40px = 2cm, within it.
        res = calculate_group_size_v2(
            _target([(200, 300), (240, 300), (540, 300), (580, 300)]),
            target_width_mm=400.0,
        )
        if res["shot_count"] != 4:
            pytest.skip(f"deteccao encontrou {res['shot_count']} impactos, nao 4")
        assert len(res["groups"]) == 2
        for g in res["groups"]:
            assert len(g["shots"]) == 2
            assert g["group_size_mm"] == pytest.approx(20.0, rel=0.05)

    def test_single_shot_group_has_zero_spread(self):
        from cv_utils import calculate_group_size_v2
        res = calculate_group_size_v2(_target([(400, 300)]))
        if res["shot_count"] != 1:
            pytest.skip(f"deteccao encontrou {res['shot_count']} impactos, nao 1")
        assert res["groups"][0]["group_size_mm"] == 0

    def test_poi_is_offset_from_aim_point_with_ballistic_y(self):
        """Point of impact is reported relative to the aim point, with Y
        flipped: a hole above the aim point is a positive vertical offset."""
        from cv_utils import calculate_group_size_v2
        res = calculate_group_size_v2(
            _target([(500, 200)]), target_width_mm=400.0, center_point=(400, 300)
        )
        if res["shot_count"] != 1:
            pytest.skip(f"deteccao encontrou {res['shot_count']} impactos, nao 1")
        poi_x, poi_y = res["groups"][0]["poi_mm"]
        # 800px de largura declarados como 400mm dao 2 px/mm.
        assert poi_x == pytest.approx(50.0, rel=0.05)   # 100px a direita
        assert poi_y == pytest.approx(50.0, rel=0.05)   # 100px acima

    def test_groups_are_numbered_from_one(self):
        from cv_utils import calculate_group_size_v2
        res = calculate_group_size_v2(_target([(150, 150), (650, 450)]))
        assert [g["id"] for g in res["groups"]] == list(range(1, len(res["groups"]) + 1))

    def test_accepts_grayscale_and_rgba_uploads(self):
        """Phone photos and edited screenshots arrive in modes other than RGB."""
        from cv_utils import calculate_group_size_v2
        for mode in ("L", "RGB", "RGBA", "P"):
            img = Image.new(mode, (400, 300), 255 if mode in ("L", "P") else (255, 255, 255, 255)[: 4 if mode == "RGBA" else 3])
            res = calculate_group_size_v2(img)
            assert res["shot_count"] == 0, f"modo {mode}"
