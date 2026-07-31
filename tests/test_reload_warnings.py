"""Tests for the reload-log safety warnings.

These warnings existed since #31 and were never visible. The save branch drew
them and then called st.rerun(), which redraws the page from scratch and
discards everything written in that pass — so the warning flashed for a
fraction of a second and vanished, while the session saved regardless. A
browser session logging .308 Winchester with CBC 216 got no warning at all
and a stored row.

Collecting them as data instead of drawing them lets the result cross the
rerun in session_state, and makes the decision testable without Streamlit.
"""

from unittest.mock import MagicMock, patch

import pytest

from components.logbook_inventory import BLOCKING, CAUTION, collect_reload_warnings


def _texts(warnings):
    return " | ".join(text for _, text in warnings)


def _severities(warnings):
    return [severity for severity, _ in warnings]


class TestSeriesViolation:
    def test_handgun_powder_in_a_rifle_cartridge_blocks(self):
        """The one combination CBC forbids outright."""
        warnings = collect_reload_warnings(".308 WINCHESTER", "CBC 216", None)
        assert BLOCKING in _severities(warnings)
        assert "gravissimos" in _texts(warnings)

    def test_rifle_powder_in_a_handgun_cartridge_blocks(self):
        warnings = collect_reload_warnings("9mm Luger", "CBC 126", None)
        assert BLOCKING in _severities(warnings)
        assert "Serie 100" in _texts(warnings)


class TestProvenance:
    def test_unreferenced_and_faster_blocks(self):
        warnings = collect_reload_warnings(".357 MAGNUM", "CBC 216", None)
        assert BLOCKING in _severities(warnings)

    def test_unreferenced_but_slower_only_cautions(self):
        warnings = collect_reload_warnings(".308 WINCHESTER", "CBC 126", None)
        assert warnings
        assert BLOCKING not in _severities(warnings)
        assert CAUTION in _severities(warnings)


class TestPrimerAndUsage:
    def test_wrong_primer_size_cautions(self):
        warnings = collect_reload_warnings(".308 WINCHESTER", "CBC 102", "Small Pistol")
        assert "Large Rifle" in _texts(warnings)

    def test_usage_restriction_is_carried(self):
        warnings = collect_reload_warnings(".44 - 40 WINCHESTER", None, None)
        assert "NAO USE ESTAS CARGAS EM REVOLVERES" in _texts(warnings)

    def test_military_ammunition_note_is_carried(self):
        warnings = collect_reload_warnings(".308 WINCHESTER", "CBC 102", None)
        assert "militar" in _texts(warnings)


class TestQuietCases:
    def test_a_correct_entry_produces_nothing(self):
        assert collect_reload_warnings("9mm Luger", "CBC 231", "Small Pistol") == []

    def test_unknown_inputs_produce_nothing(self):
        """Silence has to mean 'no information', not 'approved'."""
        assert collect_reload_warnings(".338 Lapua", "IMR 4064", None) == []
        assert collect_reload_warnings(None, None, None) == []
        assert collect_reload_warnings("", "", "") == []


class TestCombinations:
    def test_every_applicable_warning_is_reported(self):
        """The browser case: wrong powder series, wrong primer, and a
        cartridge carrying a usage restriction, all at once."""
        warnings = collect_reload_warnings(".308 WINCHESTER", "CBC 216", "Small Pistol")
        assert len(warnings) == 3
        text = _texts(warnings)
        assert "gravissimos" in text
        assert "Large Rifle" in text
        assert "militar" in text

    def test_the_blocking_warning_comes_first(self):
        """It is the one that must be read if only one is."""
        warnings = collect_reload_warnings(".308 WINCHESTER", "CBC 216", "Small Pistol")
        assert warnings[0][0] == BLOCKING

    def test_returns_plain_data_so_it_survives_a_rerun(self):
        """Anything drawn before st.rerun() is discarded; only values kept in
        session_state make it to the next pass."""
        warnings = collect_reload_warnings(".308 WINCHESTER", "CBC 216", "Small Pistol")
        assert all(
            isinstance(severity, str) and isinstance(text, str)
            for severity, text in warnings
        )


class TestDeductionHandoff:
    """What left the stock only exists in the save branch. The session list
    confirms the record, but nothing else says how much powder and how many
    primers were debited — so it has to cross the rerun too."""

    def _render(self, state):
        import components.logbook_inventory as mod

        calls = []
        fake = MagicMock()
        fake.session_state = state
        fake.success.side_effect = lambda m: calls.append(("success", m))
        fake.caption.side_effect = lambda m: calls.append(("caption", m))
        fake.expander.return_value.__enter__ = lambda s: None
        fake.expander.return_value.__exit__ = lambda s, *a: None
        with patch.object(mod, "st", fake):
            mod._render_pending_deductions()
        return calls

    def test_reports_what_was_debited(self):
        state = {"reload_deductions": ["Pólvora CBC 216: -180g", "Espoleta: -50un"]}
        calls = self._render(state)
        assert any("2 item(ns)" in m for kind, m in calls if kind == "success")

    def test_an_empty_deduction_list_still_confirms_the_save(self):
        """Distinct from 'no save happened' — the user pressed save and
        nothing matched their stock, which they should be told."""
        calls = self._render({"reload_deductions": []})
        assert any(kind == "success" for kind, _ in calls)
        assert any("Nenhum insumo" in m for kind, m in calls if kind == "caption")

    def test_nothing_is_drawn_when_no_save_happened(self):
        assert self._render({}) == []

    def test_the_record_is_consumed_so_it_shows_once(self):
        state = {"reload_deductions": ["Pólvora: -180g"]}
        self._render(state)
        assert "reload_deductions" not in state


class TestWarningHandoff:
    def test_warnings_are_consumed_so_they_show_once(self):
        import components.logbook_inventory as mod

        state = {"reload_warnings": [(BLOCKING, "perigo")]}
        fake = MagicMock()
        fake.session_state = state
        with patch.object(mod, "st", fake):
            mod._render_pending_reload_warnings()
        assert "reload_warnings" not in state
        fake.error.assert_called_once()

    def test_nothing_is_drawn_without_pending_warnings(self):
        import components.logbook_inventory as mod

        fake = MagicMock()
        fake.session_state = {}
        with patch.object(mod, "st", fake):
            mod._render_pending_reload_warnings()
        fake.error.assert_not_called()
        fake.warning.assert_not_called()
