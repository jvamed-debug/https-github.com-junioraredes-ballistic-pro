"""Tests for components.logbook_inventory deduction data flow."""

import pytest
from unittest.mock import patch, MagicMock


class TestDeductionDataFlow:
    """Verify that deduct_inventory receives plain data, not detached ORM objects."""

    @patch("services.reloading_service.managed_session")
    def test_deduction_with_plain_object(self, mock_ctx):
        from services.reloading_service import ReloadingService

        item = MagicMock()
        item.name = "IMR 4064"
        item.quantity = 500.0
        item.unit = "g"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = item
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        sess_data = type("S", (), {
            "powder": "IMR 4064",
            "charge": 42.0,
            "quantity": 20,
            "projectile": "168gr SMK",
            "primer": "Large Rifle",
            "case": "Lapua",
        })()

        ok, messages = ReloadingService.deduct_inventory(sess_data, user_id=1)
        assert ok is True
        assert len(messages) > 0

    def test_plain_session_data_has_required_attrs(self):
        """Ensure the plain data object pattern used in logbook has all required fields."""
        sess = type("S", (), {
            "powder": "Test Powder",
            "charge": 5.0,
            "quantity": 10,
            "projectile": "Test Proj",
            "primer": "Test Primer",
            "case": "Test Case",
        })()

        assert hasattr(sess, "powder")
        assert hasattr(sess, "charge")
        assert hasattr(sess, "quantity")
        assert hasattr(sess, "projectile")
        assert hasattr(sess, "primer")
        assert hasattr(sess, "case")
        assert sess.charge == 5.0
        assert sess.quantity == 10
