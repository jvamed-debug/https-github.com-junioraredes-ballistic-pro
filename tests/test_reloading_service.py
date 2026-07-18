"""Tests for services.reloading_service module."""

import pytest
from unittest.mock import patch, MagicMock


class TestDeductInventory:
    def _make_session_data(self, **kwargs):
        defaults = {
            "powder": "IMR 4064",
            "charge": 42.0,
            "quantity": 20,
            "projectile": "168gr SMK",
            "primer": "Large Rifle",
            "case": "Lapua",
        }
        defaults.update(kwargs)
        return type("SessionData", (), defaults)()

    @patch("services.reloading_service.managed_session")
    def test_deduct_sufficient_stock(self, mock_ctx):
        from services.reloading_service import ReloadingService

        item = MagicMock()
        item.name = "Test Component"
        item.quantity = 500.0
        item.unit = "g"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = item
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        session_data = self._make_session_data()
        ok, messages = ReloadingService.deduct_inventory(session_data, user_id=1)

        assert ok is True
        assert len(messages) > 0

    @patch("services.reloading_service.managed_session")
    def test_insufficient_stock_warns(self, mock_ctx):
        from services.reloading_service import ReloadingService

        powder_item = MagicMock()
        powder_item.name = "IMR 4064"
        powder_item.quantity = 1.0
        powder_item.unit = "g"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = powder_item
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        session_data = self._make_session_data(charge=42.0, quantity=100)
        ok, messages = ReloadingService.deduct_inventory(session_data, user_id=1)

        assert ok is True
        assert any("insuficiente" in m.lower() for m in messages)

    @patch("services.reloading_service.managed_session")
    def test_none_charge_handled(self, mock_ctx):
        from services.reloading_service import ReloadingService

        powder_item = MagicMock()
        powder_item.name = "Test Powder"
        powder_item.quantity = 500.0
        powder_item.unit = "g"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = powder_item
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        session_data = self._make_session_data(charge=None, quantity=20)
        ok, messages = ReloadingService.deduct_inventory(session_data, user_id=1)
        assert ok is True

    @patch("services.reloading_service.managed_session")
    def test_no_components_in_inventory(self, mock_ctx):
        from services.reloading_service import ReloadingService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        session_data = self._make_session_data()
        ok, messages = ReloadingService.deduct_inventory(session_data, user_id=1)

        assert ok is True
        assert len(messages) == 0

    @patch("services.reloading_service.managed_session")
    def test_no_powder_skips_deduction(self, mock_ctx):
        from services.reloading_service import ReloadingService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        session_data = self._make_session_data(powder=None, projectile=None, primer=None, case=None)
        ok, messages = ReloadingService.deduct_inventory(session_data, user_id=1)

        assert ok is True
        assert len(messages) == 0


class TestCalculateUnitCost:
    @patch("services.reloading_service.managed_session")
    def test_no_inventory_returns_zero(self, mock_ctx):
        from services.reloading_service import ReloadingService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        session_data = type("S", (), {
            "powder": "Test", "charge": 5.0, "projectile": "Test",
            "primer": "Test", "case": "Test"
        })()

        cost = ReloadingService.calculate_unit_cost(session_data, user_id=1)
        assert cost == 0

    @patch("services.reloading_service.managed_session")
    def test_with_inventory_calculates_cost(self, mock_ctx):
        from services.reloading_service import ReloadingService

        powder = MagicMock()
        powder.unit = "grains"
        powder.price_unit = 0.05

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = powder
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        session_data = type("S", (), {
            "powder": "Test", "charge": 10.0, "projectile": "Test",
            "primer": "Test", "case": "Test"
        })()

        cost = ReloadingService.calculate_unit_cost(session_data, user_id=1)
        assert cost > 0
