"""Testes do cartao de DOPE: correcao de torre em cliques e compensacao de
angulo. A trajetoria em si e coberta por outros testes; aqui olhamos so a
traducao de queda/deriva para o que se dial na mira."""

import math

import pytest

from services.trajectory_service import (
    DopeEntry,
    ProjectileData,
    TrajectoryPoint,
    TrajectoryResult,
    build_dope_card,
    calculate_trajectory,
)


def _result_with(points):
    return TrajectoryResult(points=points, zero_range_m=100.0)


class TestElevationComeUp:
    def test_come_up_is_positive_past_zero(self):
        """Depois do zero o projetil cai, entao a correcao e para cima."""
        pts = [TrajectoryPoint(
            range_m=300, drop_cm=-90.0, drop_moa=-10.31, drop_mil=-3.0,
            velocity_ms=400, velocity_fps=1312, energy_j=0, energy_ftlbs=0,
            time_of_flight_s=0.4,
        )]
        card = build_dope_card(_result_with(pts), unit="MIL", click_value=0.1)
        assert card[0].elevation == pytest.approx(3.0, abs=0.01)
        assert card[0].elevation_clicks == 30  # 3.0 mil / 0.1

    def test_moa_and_clicks_use_quarter_moa(self):
        pts = [TrajectoryPoint(
            range_m=200, drop_cm=-20.0, drop_moa=-3.44, drop_mil=-1.0,
            velocity_ms=500, velocity_fps=1640, energy_j=0, energy_ftlbs=0,
            time_of_flight_s=0.25,
        )]
        card = build_dope_card(_result_with(pts), unit="MOA", click_value=0.25)
        assert card[0].unit == "MOA"
        assert card[0].elevation == pytest.approx(3.44, abs=0.02)
        # 3.44 MOA / 0.25 por clique -> 14 cliques (arredondado)
        assert card[0].elevation_clicks == round(3.44 / 0.25)


class TestWindage:
    def test_drift_right_is_corrected_left(self):
        pts = [TrajectoryPoint(
            range_m=300, drop_cm=-90.0, drop_moa=-10.31, drop_mil=-3.0,
            velocity_ms=400, velocity_fps=1312, energy_j=0, energy_ftlbs=0,
            time_of_flight_s=0.4, wind_drift_cm=30.0, wind_drift_moa=3.44,
        )]
        card = build_dope_card(_result_with(pts), unit="MIL", click_value=0.1)
        assert card[0].windage_dir == "E"
        assert card[0].windage == pytest.approx(1.0, abs=0.01)  # 30cm@300m = 1 mil
        assert card[0].windage_clicks == 10

    def test_drift_left_is_corrected_right(self):
        pts = [TrajectoryPoint(
            range_m=300, drop_cm=-90.0, drop_moa=0, drop_mil=0,
            velocity_ms=400, velocity_fps=1312, energy_j=0, energy_ftlbs=0,
            time_of_flight_s=0.4, wind_drift_cm=-30.0,
        )]
        card = build_dope_card(_result_with(pts), unit="MIL", click_value=0.1)
        assert card[0].windage_dir == "D"
        assert card[0].windage == pytest.approx(1.0, abs=0.01)

    def test_no_wind_has_no_direction(self):
        pts = [TrajectoryPoint(
            range_m=300, drop_cm=-90.0, drop_moa=0, drop_mil=0,
            velocity_ms=400, velocity_fps=1312, energy_j=0, energy_ftlbs=0,
            time_of_flight_s=0.4, wind_drift_cm=0.0,
        )]
        card = build_dope_card(_result_with(pts), unit="MIL", click_value=0.1)
        assert card[0].windage_dir == "-"
        assert card[0].windage_clicks == 0


class TestInclineCompensation:
    def _one(self, incline):
        pts = [TrajectoryPoint(
            range_m=400, drop_cm=-160.0, drop_moa=0, drop_mil=-4.0,
            velocity_ms=350, velocity_fps=1148, energy_j=0, energy_ftlbs=0,
            time_of_flight_s=0.6,
        )]
        return build_dope_card(_result_with(pts), unit="MIL", click_value=0.1,
                               incline_deg=incline)[0]

    def test_level_shot_is_unchanged(self):
        assert self._one(0).elevation == pytest.approx(4.0, abs=0.01)

    def test_uphill_reduces_come_up(self):
        flat = self._one(0).elevation
        up = self._one(30).elevation
        assert up < flat
        assert up == pytest.approx(4.0 * math.cos(math.radians(30)), abs=0.01)

    def test_uphill_and_downhill_are_symmetric(self):
        """cos(+a) == cos(-a): subir ou descer 30 graus pede a mesma elevacao."""
        assert self._one(30).elevation == pytest.approx(self._one(-30).elevation, abs=0.001)

    def test_windage_is_not_affected_by_incline(self):
        pts = [TrajectoryPoint(
            range_m=400, drop_cm=-160.0, drop_moa=0, drop_mil=-4.0,
            velocity_ms=350, velocity_fps=1148, energy_j=0, energy_ftlbs=0,
            time_of_flight_s=0.6, wind_drift_cm=40.0,
        )]
        flat = build_dope_card(_result_with(pts), unit="MIL", incline_deg=0)[0]
        steep = build_dope_card(_result_with(pts), unit="MIL", incline_deg=45)[0]
        assert flat.windage == steep.windage


class TestEndToEnd:
    def test_card_matches_a_real_trajectory(self):
        """Da entrada de projetil ao cartao, sem numeros plantados."""
        proj = ProjectileData(weight_grains=168, bc_g1=0.462, muzzle_velocity_fps=2650)
        result = calculate_trajectory(proj, zero_range_m=100, max_range_m=300, step_m=100)
        card = build_dope_card(result, unit="MIL", click_value=0.1)
        assert len(card) == len(result.points)
        #  No zero a elevacao e ~0; alem dele, cresce monotonicamente.
        past_zero = [e for e in card if e.range_m > 100]
        assert all(e.elevation >= 0 for e in past_zero)
        assert past_zero == sorted(past_zero, key=lambda e: e.range_m)
        elevs = [e.elevation for e in past_zero]
        assert elevs == sorted(elevs)
