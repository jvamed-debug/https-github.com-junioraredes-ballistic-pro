from pydantic import BaseModel, EmailStr, constr, field_validator
from typing import Optional
from datetime import date

class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=50)
    password: constr(min_length=8)
    name: Optional[str] = None
    cpf: Optional[constr(pattern=r"^\d{11}$")] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    cr_number: Optional[str] = None
    cr_expiration: Optional[date] = None
    address_acervo: Optional[str] = None

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    cpf: Optional[constr(pattern=r"^\d{11}$")] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    cr_number: Optional[str] = None
    cr_expiration: Optional[date] = None
    address_acervo: Optional[str] = None

class InventoryItemCreate(BaseModel):
    category: constr(min_length=3, max_length=50)
    name: constr(min_length=1, max_length=100)
    quantity: float
    unit: constr(min_length=1, max_length=10)
    price_unit: Optional[float] = 0.0
    batch_number: Optional[str] = None
    expiration_date: Optional[date] = None

    @field_validator("quantity")
    @classmethod
    def quantity_non_negative(cls, v):
        if v < 0:
            raise ValueError("Quantidade não pode ser negativa")
        return v

class FirearmCreate(BaseModel):
    model: constr(min_length=2, max_length=100)
    serial: Optional[str] = None
    sigma: Optional[str] = None
    craf: Optional[str] = None
    expiration: Optional[date] = None

class ReloadSessionCreate(BaseModel):
    caliber: constr(min_length=2)
    quantity: int
    charge: Optional[float] = 0.0
    velocity_avg: Optional[float] = 0.0
    velocity_sd: Optional[float] = 0.0
    powder: Optional[str] = None
    projectile: Optional[str] = None
    primer: Optional[str] = None
    case: Optional[str] = None
    firearm_id: Optional[int] = None

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v):
        if v < 1:
            raise ValueError("Quantidade deve ser pelo menos 1")
        return v

    @field_validator("charge", "velocity_avg", "velocity_sd")
    @classmethod
    def non_negative_floats(cls, v):
        if v is not None and v < 0:
            raise ValueError("Valor não pode ser negativo")
        return v