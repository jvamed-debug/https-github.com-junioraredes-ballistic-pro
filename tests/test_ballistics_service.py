"""Tests for the ballistics service."""

import json
import os

import pytest

from services.ballistics_service import BallisticsService


def test_load_data():
    data = BallisticsService.load_data()
    assert "calibers" in data
    assert len(data["calibers"]) > 0


def test_get_calibers():
    calibers = BallisticsService.get_calibers()
    assert isinstance(calibers, list)
    assert len(calibers) > 0
    assert "9mm Luger" in calibers or len(calibers) > 5


def test_get_caliber_details():
    calibers = BallisticsService.get_calibers()
    if calibers:
        details = BallisticsService.get_caliber_details(calibers[0])
        assert isinstance(details, dict)


def test_get_caliber_details_unknown():
    details = BallisticsService.get_caliber_details("NONEXISTENT_CALIBER")
    assert details == {}


def test_calculate_predicted_load():
    result = BallisticsService.calculate_predicted_load(1000, 10, 1200)
    assert result == 12.0


def test_calculate_predicted_load_zero_velocity():
    result = BallisticsService.calculate_predicted_load(0, 10, 1200)
    assert result == 0


def test_database_json_structure():
    path = "database.json"
    assert os.path.exists(path), "database.json must exist"

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "calibers" in data

    for cal_name, cal_data in data["calibers"].items():
        assert "projectiles" in cal_data, f"{cal_name} missing projectiles"
        for proj_name, proj_data in cal_data["projectiles"].items():
            assert "powders" in proj_data, f"{cal_name}/{proj_name} missing powders"
            for pow_name, pow_data in proj_data["powders"].items():
                assert "min" in pow_data, f"{cal_name}/{proj_name}/{pow_name} missing min"
                assert "max" in pow_data, f"{cal_name}/{proj_name}/{pow_name} missing max"
                assert pow_data["min"] <= pow_data["max"], (
                    f"{cal_name}/{proj_name}/{pow_name}: min ({pow_data['min']}) > max ({pow_data['max']})"
                )


class TestMuzzleEnergy:
    def test_known_load_matches_published_energy(self):
        """.38 Special 158gr at 750 fps is published at roughly 197 ft-lbf,
        which is 267 J."""
        e = BallisticsService.muzzle_energy_joules(158, 750)
        assert e == pytest.approx(267.5, rel=0.01)

    def test_rifle_load_matches_published_energy(self):
        """.30-06 168gr at 2700 fps is published at roughly 2719 ft-lbf."""
        e = BallisticsService.muzzle_energy_joules(168, 2700)
        assert e == pytest.approx(3687, rel=0.01)

    def test_energy_scales_with_the_square_of_velocity(self):
        single = BallisticsService.muzzle_energy_joules(150, 1000)
        double = BallisticsService.muzzle_energy_joules(150, 2000)
        assert double == pytest.approx(single * 4)

    def test_energy_scales_linearly_with_mass(self):
        light = BallisticsService.muzzle_energy_joules(100, 1200)
        heavy = BallisticsService.muzzle_energy_joules(200, 1200)
        assert heavy == pytest.approx(light * 2)

    def test_zero_velocity_is_zero_energy(self):
        assert BallisticsService.muzzle_energy_joules(158, 0) == 0


class TestEstimateCharge:
    def test_pistol_estimate_is_close_to_published_data(self):
        """.38 Special 158gr at 750 fps runs about 3.5 to 4.5 grains of a fast
        powder in the published tables; the model lands inside that."""
        gr = BallisticsService.estimate_charge_grains(158, 750, 3800, 25)
        assert 3.5 <= gr <= 5.0

    def test_rifle_estimate_is_the_right_order_but_runs_high(self):
        """.30-06 168gr at 2700 fps is about 45 to 48 grains of IMR 4064. The
        model returns roughly 60 — right order of magnitude, but a quarter
        over, because it ignores the pressure curve and burn time. Pinned so
        the gap stays visible rather than being mistaken for a load figure."""
        gr = BallisticsService.estimate_charge_grains(168, 2700, 3800, 25)
        assert gr == pytest.approx(59.9, rel=0.02)
        assert gr > 48, "modelo subestimando: a margem de seguranca inverteria"

    def test_higher_efficiency_needs_less_powder(self):
        low = BallisticsService.estimate_charge_grains(158, 750, 3800, 20)
        high = BallisticsService.estimate_charge_grains(158, 750, 3800, 40)
        assert high == pytest.approx(low / 2)

    def test_more_energetic_powder_needs_less_of_it(self):
        weak = BallisticsService.estimate_charge_grains(158, 750, 3000, 25)
        strong = BallisticsService.estimate_charge_grains(158, 750, 6000, 25)
        assert strong == pytest.approx(weak / 2)

    def test_zero_or_negative_inputs_return_zero_rather_than_dividing(self):
        assert BallisticsService.estimate_charge_grains(158, 750, 0, 25) == 0.0
        assert BallisticsService.estimate_charge_grains(158, 750, 3800, 0) == 0.0
        assert BallisticsService.estimate_charge_grains(158, 750, -1, 25) == 0.0

    def test_conversion_factors_are_the_exact_definitions(self):
        """A drift here silently rescales every charge the calculator shows."""
        assert BallisticsService.GRAIN_TO_KG == pytest.approx(1 / 15432.358, rel=1e-4)
        assert BallisticsService.GRAM_TO_GRAIN == pytest.approx(15.4324, rel=1e-5)
        assert BallisticsService.FPS_TO_MS == 0.3048

    def test_grain_and_gram_factors_round_trip(self):
        grains = 158.0
        kg = grains * BallisticsService.GRAIN_TO_KG
        back = (kg * 1000) * BallisticsService.GRAM_TO_GRAIN
        assert back == pytest.approx(grains, rel=1e-4)
