"""Tests for the cartridge specification registry.

Reference values come from Revista Magnum, Manual de Recarga de Municoes,
Edicao Especial no 44.
"""

import pytest

from services.cartridge_specs import (
    LARGE_PISTOL,
    SMALL_PISTOL,
    SPECS,
    check_overall_length,
    check_primer_size,
    get_spec,
)


class TestRegistry:
    def test_pressures_match_the_manual(self):
        assert SPECS[".357 MAGNUM"].max_pressure_cup == 45_000
        assert SPECS[".357 MAGNUM"].max_pressure_psi == 35_000
        assert SPECS[".44 REM. MAGNUM"].max_pressure_cup == 40_000
        assert SPECS[".38 SPL"].max_pressure_cup == 17_000
        assert SPECS["9mm Luger"].max_pressure_psi == 35_000
        assert SPECS[".45 AUTO"].max_pressure_psi == 22_000

    def test_overall_lengths_match_the_manual(self):
        assert SPECS[".357 MAGNUM"].max_oal_mm == 40.39
        assert SPECS["9mm Luger"].max_oal_mm == 29.69
        assert SPECS[".45 AUTO"].max_oal_mm == 32.39

    def test_primer_sizes_match_the_manual(self):
        assert SPECS[".45 AUTO"].primer == LARGE_PISTOL
        assert SPECS[".44 REM. MAGNUM"].primer == LARGE_PISTOL
        assert SPECS["9mm Luger"].primer == SMALL_PISTOL
        assert SPECS[".38 SPL"].primer == SMALL_PISTOL

    def test_cup_and_psi_are_kept_separate(self):
        """The two scales measure different things and do not convert into
        one another; storing one as the other would invent a number."""
        spl = SPECS[".38 S&W"]
        assert spl.max_pressure_cup == 13_000
        assert spl.max_pressure_psi is None

    def test_plus_p_limits_are_recorded_where_they_exist(self):
        assert SPECS[".38 SPL"].accepts_plus_p
        assert SPECS[".38 SPL"].max_pressure_cup_plus_p == 20_000
        assert SPECS["9mm Luger"].max_pressure_psi_plus_p == 38_500
        assert not SPECS[".32 S&W"].accepts_plus_p

    def test_lookup_is_case_insensitive(self):
        assert get_spec("9MM LUGER").name == "9mm Luger"
        assert get_spec(".45 auto").name == ".45 AUTO"

    def test_unknown_cartridge_is_none(self):
        assert get_spec(".338 Lapua") is None
        assert get_spec(None) is None


class TestOverallLength:
    def test_flags_a_cartridge_longer_than_the_maximum(self):
        warning = check_overall_length("9mm Luger", 31.0)
        assert warning is not None
        assert "29.69" in warning

    def test_accepts_a_cartridge_at_or_under_the_maximum(self):
        assert check_overall_length("9mm Luger", 29.69) is None
        assert check_overall_length("9mm Luger", 28.0) is None

    def test_silent_without_a_basis(self):
        assert check_overall_length(".338 Lapua", 90.0) is None
        assert check_overall_length("9mm Luger", None) is None
        assert check_overall_length("9mm Luger", 0) is None


class TestPrimerSize:
    def test_flags_large_primer_in_a_small_primer_cartridge(self):
        warning = check_primer_size("9mm Luger", "CBC Large Pistol 2 1/2")
        assert warning is not None
        assert SMALL_PISTOL in warning

    def test_flags_small_primer_in_a_large_primer_cartridge(self):
        warning = check_primer_size(".45 AUTO", "Small Pistol 1 1/2")
        assert warning is not None
        assert LARGE_PISTOL in warning

    def test_correct_primer_is_silent(self):
        assert check_primer_size("9mm Luger", "CBC Small Pistol 1 1/2") is None
        assert check_primer_size(".45 AUTO", "CBC 2 1/2 Large Pistol") is None

    def test_unrecognised_primer_text_is_silent(self):
        """Free text that names no size gives nothing to check."""
        assert check_primer_size("9mm Luger", "CBC 1 1/2") is None
        assert check_primer_size("9mm Luger", "") is None
