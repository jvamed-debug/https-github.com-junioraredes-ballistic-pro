"""Tests for the CBC powder registry and its safety checks.

Reference values come from the CBC Manual de Recarga: the Serie 100 / Serie
200 split, the vivacidade (burn rate) ordering, and the gravimetric density
table.
"""

import json

import pytest

from services.cbc_powders import (
    HANDGUN,
    POWDERS,
    RIFLE,
    SERIES_100,
    SERIES_200,
    check_powder_for_caliber,
    compare_burn_rate,
    get_cartridge_type,
    get_powder,
)


class TestRegistry:
    def test_every_powder_in_the_manual_is_present(self):
        expected = {
            "CBC 102", "CBC 124", "CBC 126", "CBC 128", "CBC 129",
            "CBC 207", "CBC 210", "CBC 212", "CBC 216", "CBC 217",
            "CBC 218", "CBC 219", "CBC 220", "CBC 222", "CBC 231",
            "CBC 236", "CBC 244", "CBC 246", "CBC 250", "CBC 266",
        }
        assert set(POWDERS) == expected

    def test_series_100_is_rifle_only(self):
        for name in ("CBC 102", "CBC 124", "CBC 126", "CBC 128", "CBC 129"):
            p = POWDERS[name]
            assert p.series == SERIES_100
            assert p.intended_use == RIFLE

    def test_series_200_is_handgun(self):
        for name in ("CBC 207", "CBC 216", "CBC 231", "CBC 244", "CBC 250"):
            p = POWDERS[name]
            assert p.series == SERIES_200
            assert p.intended_use == HANDGUN

    def test_burn_ranks_are_unique_within_each_series(self):
        for series in (SERIES_100, SERIES_200):
            ranks = [p.burn_rank for p in POWDERS.values() if p.series == series]
            assert sorted(ranks) == list(range(1, len(ranks) + 1))

    def test_fastest_and_slowest_match_the_manual_scale(self):
        """Serie 200 runs 216 (fastest) to 244 (slowest); Serie 100 runs 129
        to 124."""
        s200 = [p for p in POWDERS.values() if p.series == SERIES_200]
        s100 = [p for p in POWDERS.values() if p.series == SERIES_100]
        assert min(s200, key=lambda p: p.burn_rank).name == "CBC 216"
        assert max(s200, key=lambda p: p.burn_rank).name == "CBC 244"
        assert min(s100, key=lambda p: p.burn_rank).name == "CBC 129"
        assert max(s100, key=lambda p: p.burn_rank).name == "CBC 124"

    def test_bulk_densities_are_within_the_published_ranges(self):
        assert POWDERS["CBC 124"].bulk_density_g_per_l == pytest.approx(930, abs=30)
        assert POWDERS["CBC 250"].bulk_density_g_per_l == pytest.approx(400, abs=1)
        assert POWDERS["CBC 216"].bulk_density_g_per_l == pytest.approx(480, abs=1)


class TestLookup:
    def test_finds_a_powder_regardless_of_case_and_spacing(self):
        for spelling in ("CBC 216", "cbc 216", "  CBC   216  "):
            assert get_powder(spelling).name == "CBC 216"

    def test_unknown_powder_is_none(self):
        assert get_powder("IMR 4064") is None
        assert get_powder("") is None
        assert get_powder(None) is None

    def test_cartridge_lookup_is_case_insensitive(self):
        assert get_cartridge_type(".308 winchester") == RIFLE
        assert get_cartridge_type("9MM LUGER") == HANDGUN

    def test_unknown_cartridge_is_none(self):
        assert get_cartridge_type(".338 Lapua") is None
        assert get_cartridge_type(None) is None


class TestSeriesCheck:
    def test_handgun_powder_in_a_rifle_cartridge_is_flagged(self):
        """The manual calls this out as capable of causing 'incidentes
        gravissimos'."""
        warning = check_powder_for_caliber(".308 WINCHESTER", "CBC 216")
        assert warning is not None
        assert "Serie 200" in warning
        assert "gravissimos" in warning

    def test_rifle_powder_in_a_handgun_cartridge_is_flagged(self):
        warning = check_powder_for_caliber("9mm Luger", "CBC 126")
        assert warning is not None
        assert "Serie 100" in warning

    def test_correct_pairings_are_silent(self):
        assert check_powder_for_caliber(".308 WINCHESTER", "CBC 102") is None
        assert check_powder_for_caliber("9mm Luger", "CBC 231") is None

    def test_silence_when_there_is_no_basis_to_judge(self):
        """Not knowing a powder or a cartridge must read as 'no information',
        never as approval."""
        assert check_powder_for_caliber(".308 WINCHESTER", "IMR 4064") is None
        assert check_powder_for_caliber(".338 Lapua", "CBC 216") is None
        assert check_powder_for_caliber(None, None) is None


class TestBurnRateComparison:
    def test_switching_to_a_faster_powder_warns(self):
        warning = compare_burn_rate("CBC 244", "CBC 216")
        assert warning is not None
        assert "carga minima" in warning

    def test_switching_to_a_slower_powder_is_silent(self):
        assert compare_burn_rate("CBC 216", "CBC 244") is None

    def test_same_powder_is_silent(self):
        assert compare_burn_rate("CBC 216", "CBC 216") is None

    def test_no_comparison_across_series(self):
        """A cross-series swap is the series check's job, not this one."""
        assert compare_burn_rate("CBC 126", "CBC 216") is None

    def test_unknown_powders_are_silent(self):
        assert compare_burn_rate("IMR 4064", "CBC 216") is None


class TestCatalogueRespectsTheSeriesRule:
    def test_no_shipped_load_pairs_a_cartridge_with_the_wrong_series(self):
        """Guards the reference catalogue itself against a bad edit."""
        data = json.load(open("database.json", encoding="utf-8"))
        violations = []
        for caliber, cal_data in data["calibers"].items():
            for projectile, proj_data in cal_data.get("projectiles", {}).items():
                for powder in proj_data.get("powders", {}):
                    if check_powder_for_caliber(caliber, powder):
                        violations.append(f"{caliber} + {powder}")
        assert violations == []

    def test_every_catalogued_caliber_and_powder_is_classified(self):
        """Otherwise the check above passes by knowing nothing."""
        data = json.load(open("database.json", encoding="utf-8"))
        unclassified = []
        for caliber, cal_data in data["calibers"].items():
            if get_cartridge_type(caliber) is None:
                unclassified.append(caliber)
            for projectile, proj_data in cal_data.get("projectiles", {}).items():
                for powder in proj_data.get("powders", {}):
                    if get_powder(powder) is None:
                        unclassified.append(powder)
        assert sorted(set(unclassified)) == []
