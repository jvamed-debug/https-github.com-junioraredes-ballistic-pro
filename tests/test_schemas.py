"""Tests for Pydantic validation schemas."""

import pytest
from datetime import date
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

    def test_optional_fields_none(self):
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

    def test_optional_fields_omitted(self):
        user = UserCreate(username="testuser", password="securepass123")
        assert user.name is None
        assert user.email is None
        assert user.cpf is None

    def test_long_username_fails(self):
        with pytest.raises(Exception):
            UserCreate(username="a" * 51, password="securepass123")

    def test_cpf_with_letters_fails(self):
        with pytest.raises(Exception):
            UserCreate(username="testuser", password="securepass123", cpf="1234567890a")

    def test_exact_min_username(self):
        user = UserCreate(username="abc", password="12345678")
        assert user.username == "abc"

    def test_exact_min_password(self):
        user = UserCreate(username="testuser", password="12345678")
        assert user.password == "12345678"


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

    def test_negative_quantity_fails(self):
        with pytest.raises(Exception):
            InventoryItemCreate(category="Polvora", name="Test", quantity=-1.0, unit="g")

    def test_empty_name_fails(self):
        with pytest.raises(Exception):
            InventoryItemCreate(category="Polvora", name="", quantity=100, unit="g")

    def test_batch_number_optional(self):
        item = InventoryItemCreate(
            category="Espoleta",
            name="SP Magnum",
            quantity=1000.0,
            unit="un",
        )
        assert item.batch_number is None

    def test_batch_number_set(self):
        item = InventoryItemCreate(
            category="Espoleta",
            name="SP Magnum",
            quantity=1000.0,
            unit="un",
            batch_number="LOT-2025-A",
        )
        assert item.batch_number == "LOT-2025-A"

    def test_expiration_date(self):
        item = InventoryItemCreate(
            category="Polvora",
            name="Vihtavuori N340",
            quantity=200.0,
            unit="g",
            expiration_date=date(2028, 6, 30),
        )
        assert item.expiration_date == date(2028, 6, 30)

    def test_default_price_unit(self):
        item = InventoryItemCreate(
            category="Estojo",
            name="CBC .38",
            quantity=50.0,
            unit="un",
        )
        assert item.price_unit == 0.0


class TestFirearmCreate:
    def test_valid_firearm(self):
        f = FirearmCreate(model="Taurus G3C")
        assert f.model == "Taurus G3C"

    def test_short_model_fails(self):
        with pytest.raises(Exception):
            FirearmCreate(model="X")

    def test_optional_fields_default_none(self):
        f = FirearmCreate(model="Taurus G3C")
        assert f.serial is None
        assert f.sigma is None
        assert f.craf is None
        assert f.expiration is None

    def test_with_all_fields(self):
        f = FirearmCreate(
            model="Taurus PT92",
            serial="ABC123",
            sigma="SIG-001",
            craf="CRAF-002",
            expiration=date(2030, 1, 1),
        )
        assert f.serial == "ABC123"
        assert f.expiration == date(2030, 1, 1)


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
        assert s.velocity_sd == 0.0
        assert s.powder is None
        assert s.projectile is None
        assert s.primer is None
        assert s.case is None
        assert s.firearm_id is None

    def test_zero_quantity_fails(self):
        with pytest.raises(Exception):
            ReloadSessionCreate(caliber="9mm", quantity=0)

    def test_negative_quantity_fails(self):
        with pytest.raises(Exception):
            ReloadSessionCreate(caliber=".308 Win", quantity=-5)

    def test_negative_charge_fails(self):
        with pytest.raises(Exception):
            ReloadSessionCreate(caliber="9mm", quantity=50, charge=-1.0)

    def test_negative_velocity_fails(self):
        with pytest.raises(Exception):
            ReloadSessionCreate(caliber="9mm", quantity=50, velocity_avg=-100.0)

    def test_negative_velocity_sd_fails(self):
        with pytest.raises(Exception):
            ReloadSessionCreate(caliber="9mm", quantity=50, velocity_sd=-5.0)

    def test_full_session(self):
        s = ReloadSessionCreate(
            caliber=".308 Win",
            quantity=20,
            charge=42.5,
            velocity_avg=2650.0,
            velocity_sd=12.3,
            powder="IMR 4064",
            projectile="168gr SMK",
            primer="Large Rifle",
            case="Lapua",
            firearm_id=7,
        )
        assert s.powder == "IMR 4064"
        assert s.primer == "Large Rifle"
        assert s.case == "Lapua"
        assert s.firearm_id == 7
        assert s.velocity_sd == 12.3

    def test_none_charge_allowed(self):
        s = ReloadSessionCreate(caliber="9mm", quantity=10, charge=None)
        assert s.charge is None

    def test_none_velocity_allowed(self):
        s = ReloadSessionCreate(caliber="9mm", quantity=10, velocity_avg=None, velocity_sd=None)
        assert s.velocity_avg is None
        assert s.velocity_sd is None
