"""Tests for the ballistics service."""

import json
import os

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
