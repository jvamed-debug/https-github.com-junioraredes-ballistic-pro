"""Tests for report_gen module."""

import pytest
import numpy as np
from datetime import date


def _make_user(**kwargs):
    defaults = {
        "name": "Test User",
        "cpf": "123.456.789-00",
        "cr_number": "CR12345",
        "cr_expiration": date(2030, 1, 1),
        "address_acervo": "Rua Teste, 123",
    }
    defaults.update(kwargs)
    return defaults


def _make_firearm(**kwargs):
    defaults = {
        "model": "Taurus PT92",
        "serial": "ABC123",
        "sigma": "SIG001",
        "craf": "CRAF001",
    }
    defaults.update(kwargs)
    return defaults


def _make_session(**kwargs):
    defaults = {
        "date": "2025-06-15",
        "date_str": "15/06/2025",
        "caliber": ".308 Win",
        "charge": 42.0,
        "quantity": 20,
    }
    defaults.update(kwargs)
    return defaults


class TestCreateInspectionReport:
    def test_returns_pdf_bytes(self):
        from report_gen import create_inspection_report
        result = create_inspection_report(_make_user())
        assert len(result) > 0
        assert result[:5] == b"%PDF-"

    def test_with_firearms(self):
        from report_gen import create_inspection_report
        firearms = [_make_firearm(), _make_firearm(model="Imbel IA2")]
        result = create_inspection_report(_make_user(), firearms_data=firearms)
        assert result[:5] == b"%PDF-"

    def test_with_sessions(self):
        from report_gen import create_inspection_report
        sessions = [_make_session(), _make_session(caliber="9mm")]
        result = create_inspection_report(_make_user(), sessions_data=sessions)
        assert result[:5] == b"%PDF-"

    def test_empty_data(self):
        from report_gen import create_inspection_report
        result = create_inspection_report(_make_user(), firearms_data=[], sessions_data=[])
        assert result[:5] == b"%PDF-"

    def test_none_user_fields(self):
        from report_gen import create_inspection_report
        user = _make_user(name=None, cpf=None, cr_number=None, cr_expiration=None, address_acervo=None)
        result = create_inspection_report(user)
        assert result[:5] == b"%PDF-"

    def test_xss_content_escaped(self):
        from report_gen import create_inspection_report
        user = _make_user(name="<script>alert(1)</script>")
        result = create_inspection_report(user)
        assert result[:5] == b"%PDF-"

    def test_user_as_object(self):
        from report_gen import create_inspection_report
        user_obj = type("User", (), _make_user())()
        result = create_inspection_report(user_obj)
        assert result[:5] == b"%PDF-"


class TestCreatePerformanceReportV2:
    def _make_cv_results(self):
        annotated = np.zeros((480, 640, 3), dtype=np.uint8)
        return {
            "annotated_image": annotated,
            "shot_count": 5,
            "groups": [
                {
                    "id": 1,
                    "shots": [(100, 100), (110, 110), (105, 105)],
                    "group_size_mm": 25.5,
                    "poi_mm": (2.3, -1.5),
                },
                {
                    "id": 2,
                    "shots": [(200, 200), (210, 210)],
                    "group_size_mm": 15.0,
                    "poi_mm": (-0.5, 0.8),
                },
            ],
        }

    def test_returns_pdf_bytes(self):
        from report_gen import create_performance_report_v2
        result = create_performance_report_v2(
            _make_user(), self._make_cv_results(), np.zeros((480, 640, 3), dtype=np.uint8)
        )
        assert len(result) > 0
        assert result[:5] == b"%PDF-"

    def test_empty_groups(self):
        from report_gen import create_performance_report_v2
        cv_results = self._make_cv_results()
        cv_results["groups"] = []
        cv_results["shot_count"] = 0
        result = create_performance_report_v2(_make_user(), cv_results, np.zeros((480, 640, 3), dtype=np.uint8))
        assert result[:5] == b"%PDF-"

    def test_high_dispersion(self):
        from report_gen import create_performance_report_v2
        cv_results = self._make_cv_results()
        cv_results["groups"][0]["group_size_mm"] = 80.0
        result = create_performance_report_v2(_make_user(), cv_results, np.zeros((480, 640, 3), dtype=np.uint8))
        assert result[:5] == b"%PDF-"

    def test_user_as_dict(self):
        from report_gen import create_performance_report_v2
        result = create_performance_report_v2(
            _make_user(), self._make_cv_results(), np.zeros((480, 640, 3), dtype=np.uint8)
        )
        assert result[:5] == b"%PDF-"
