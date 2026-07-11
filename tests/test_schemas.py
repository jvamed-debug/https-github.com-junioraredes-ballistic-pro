"""Tests for Pydantic validation schemas."""

import pytest
from schemas import UserCreate, InventoryItemCreate, FirearmCreate, ReloadSessionCreate


class TestUserCreate:
    def test_valid_user(self):
        user = UserCreate(
            username="testuser",
            password="securepass123",
            name="Test User",
            cpf="12345678901",
            email="test@example.com",
            phone="11999999999",
            cr_number="CR-123",
            cr_expiration="2026-12-31",
            address_acervo="Rua Teste, 123",
        )
        assert user.username == "testuser"

    def test_short_username_fails(self):
        with pytest.raises(Exception):
            UserCreate(username="ab", password="securepass123")

    def test_short_password_fails(self):
        with pytest.raises(Exception):
            UserCreate(username="testuser", password="short")

    def test_invalid_cpf_fails(self):
        with pytest.raises(Exception):
            UserCreate(username="testuser", password="securepass123", cpf="123")

    def test_invalid_email_fails(self):
        with pytest.raises(Exception):
            UserCreate(username="testuser", password="securepass123", email="not-an-email")

    def test_optional_fields(self):
        user = UserCreate(
            username="testuser",
            password="securepass123",
            name=None,
            cpf=None,
            email=None,
            phone=None,
            cr_number=None,
            cr_expiration=None,
            address_acervo=None,
        )
        assert user.name is None
        assert user.cpf is None
        assert user.email is None


class TestInventoryItemCreate:
    def test_valid_item(self):
        item = InventoryItemCreate(
            category="Polvora",
            name="CBC 216",
            quantity=500.0,
            unit="g",
            price_unit=0.50,
        )
        assert item.name == "CBC 216"

    def test_zero_quantity_allowed(self):
        item = InventoryItemCreate(
            category="Projetil",
            name="147gr FMJ",
            quantity=0.0,
            unit="un",
        )
        assert item.quantity == 0.0

    def test_empty_name_fails(self):
        with pytest.raises(Exception):
            InventoryItemCreate(category="Polvora", name="", quantity=100, unit="g")


class TestFirearmCreate:
    def test_valid_firearm(self):
        f = FirearmCreate(model="Taurus G3C", serial=None, sigma=None, craf=None)
        assert f.model == "Taurus G3C"

    def test_short_model_fails(self):
        with pytest.raises(Exception):
            FirearmCreate(model="X", serial=None, sigma=None, craf=None)

    def test_optional_fields(self):
        f = FirearmCreate(model="Taurus G3C", serial=None, sigma=None, craf=None)
        assert f.serial is None
        assert f.sigma is None
        assert f.craf is None


class TestReloadSessionCreate:
    def test_valid_session(self):
        s = ReloadSessionCreate(caliber="9mm", quantity=50)
        assert s.caliber == "9mm"
        assert s.quantity == 50

    def test_short_caliber_fails(self):
        with pytest.raises(Exception):
            ReloadSessionCreate(caliber="X", quantity=50)

    def test_defaults(self):
        s = ReloadSessionCreate(caliber="9mm", quantity=50)
        assert s.charge == 0.0
        assert s.velocity_avg == 0.0
