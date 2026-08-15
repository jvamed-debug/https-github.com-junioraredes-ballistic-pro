"""Testes das correcoes de tiro longo: deriva giroscopica (spin drift),
Coriolis e o fator de estabilidade de Miller."""

import math

from services.trajectory_service import (
    ProjectileData,
    build_dope_card,
    calculate_trajectory,
    miller_stability,
)


def _proj():
    #  .308 175gr, BC G7 tipico.
    return ProjectileData(weight_grains=175, bc_g7=0.243, diameter_mm=7.82, muzzle_velocity_fps=2600)


class TestMillerStability:
    def test_zero_without_length_or_twist(self):
        assert miller_stability(175, 0.308, 0, 11, 2600) == 0.0
        assert miller_stability(175, 0.308, 1.24, 0, 2600) == 0.0

    def test_typical_308_is_well_stabilized(self):
        sg = miller_stability(175, 7.82 / 25.4, 1.24, 11, 2600)
        assert 1.4 < sg < 2.6  # bem estabilizado

    def test_slower_twist_lowers_stability(self):
        fast = miller_stability(175, 0.308, 1.24, 10, 2600)
        slow = miller_stability(175, 0.308, 1.24, 13, 2600)
        assert slow < fast


class TestSpinDrift:
    def test_right_twist_drifts_right_and_grows(self):
        r = calculate_trajectory(
            _proj(), zero_range_m=100, max_range_m=800, step_m=200,
            twist_rate_in=11, bullet_length_in=1.24, twist_dir="right",
        )
        spins = [p.spin_drift_cm for p in r.points]
        assert all(s >= 0 for s in spins)
        assert spins[-1] > spins[0] > 0  # cresce com a distancia

    def test_left_twist_is_mirror(self):
        right = calculate_trajectory(
            _proj(), zero_range_m=100, max_range_m=600, step_m=200,
            twist_rate_in=11, bullet_length_in=1.24, twist_dir="right",
        )
        left = calculate_trajectory(
            _proj(), zero_range_m=100, max_range_m=600, step_m=200,
            twist_rate_in=11, bullet_length_in=1.24, twist_dir="left",
        )
        assert left.points[-1].spin_drift_cm == -right.points[-1].spin_drift_cm

    def test_explicit_stability_overrides_twist(self):
        #  Sem passo, mas com SG informado, ainda ha deriva.
        r = calculate_trajectory(
            _proj(), zero_range_m=100, max_range_m=600, step_m=200, stability=1.9,
        )
        assert r.points[-1].spin_drift_cm > 0

    def test_no_input_means_no_spin(self):
        r = calculate_trajectory(_proj(), zero_range_m=100, max_range_m=600, step_m=200)
        assert all(p.spin_drift_cm == 0 for p in r.points)


class TestCoriolis:
    def test_no_latitude_no_effect(self):
        r = calculate_trajectory(_proj(), zero_range_m=100, max_range_m=1000, step_m=1000)
        assert r.points[-1].wind_drift_cm == 0.0

    def test_hemisphere_flips_lateral_sign(self):
        north = calculate_trajectory(
            _proj(), zero_range_m=100, max_range_m=1000, step_m=1000,
            latitude_deg=40, azimuth_deg=90,
        ).points[-1].wind_drift_cm
        south = calculate_trajectory(
            _proj(), zero_range_m=100, max_range_m=1000, step_m=1000,
            latitude_deg=-40, azimuth_deg=90,
        ).points[-1].wind_drift_cm
        assert north > 0 and south < 0
        assert math.isclose(north, -south, abs_tol=0.5)


class TestDopeIncludesSpin:
    def test_windage_total_includes_spin_drift(self):
        r = calculate_trajectory(
            _proj(), zero_range_m=100, max_range_m=800, step_m=200,
            twist_rate_in=11, bullet_length_in=1.24, twist_dir="right",
        )
        card = build_dope_card(r, unit="MIL", click_value=0.1)
        last = card[-1]
        #  Sem vento, a correcao lateral vem so da deriva giroscopica -> 'E'.
        assert last.spin_drift_cm > 0
        assert last.windage > 0
        assert last.windage_dir == "E"
