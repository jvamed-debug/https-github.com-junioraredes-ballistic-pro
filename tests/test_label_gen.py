"""Tests for label_gen module."""

import pytest
from datetime import date


def _make_session(**kwargs):
    defaults = {
        "date": date(2025, 6, 15),
        "caliber": ".308 Win",
        "projectile": "168gr SMK",
        "powder": "IMR 4064",
        "charge": 42.0,
        "quantity": 20,
        "primer": "Large Rifle",
        "case": "Lapua",
        "velocity_avg": 2650,
        "velocity_sd": None,
        "notes": "Test load",
    }
    defaults.update(kwargs)
    return type("Session", (), defaults)()


class TestCreateLabelPdf:
    def test_returns_bytes_buffer(self):
        from label_gen import create_label_pdf
        result = create_label_pdf(_make_session(), "Test User")
        data = result.read()
        assert len(data) > 0
        assert data[:5] == b"%PDF-"

    def test_none_date_no_crash(self):
        from label_gen import create_label_pdf
        result = create_label_pdf(_make_session(date=None), "Test User")
        data = result.read()
        assert len(data) > 0

    def test_none_fields_no_crash(self):
        from label_gen import create_label_pdf
        sess = _make_session(
            caliber=None, projectile=None, powder=None,
            charge=None, quantity=None, primer=None,
            case=None, velocity_avg=None, notes=None,
        )
        result = create_label_pdf(sess, "Test User")
        data = result.read()
        assert len(data) > 0

    def test_long_notes_truncated(self):
        from label_gen import create_label_pdf
        long_notes = "A" * 100
        result = create_label_pdf(_make_session(notes=long_notes), "User")
        data = result.read()
        assert len(data) > 0

    def test_empty_user_name(self):
        from label_gen import create_label_pdf
        result = create_label_pdf(_make_session(), "")
        data = result.read()
        assert len(data) > 0

    def test_with_velocity(self):
        from label_gen import create_label_pdf
        result = create_label_pdf(_make_session(velocity_avg=2650), "User")
        data = result.read()
        assert len(data) > 0

    def test_without_velocity(self):
        from label_gen import create_label_pdf
        result = create_label_pdf(_make_session(velocity_avg=None), "User")
        data = result.read()
        assert len(data) > 0
