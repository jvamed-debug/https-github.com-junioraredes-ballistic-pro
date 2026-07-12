from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import date

class UserCreate(BaseModel):
    """
    Modelo para validação de dados ao criar um novo usuário.
    """
    username: constr(min_length=3, max_length=50)
    password: constr(min_length=8)
    name: Optional[str]
    cpf: Optional[constr(pattern=r"^\d{11}$")]  # CPF com 11 dígitos
    email: Optional[EmailStr]
    phone: Optional[str]
    cr_number: Optional[str]
    cr_expiration: Optional[date]
    address_acervo: Optional[str]

class InventoryItemCreate(BaseModel):
    """
    Modelo para validação de dados ao criar um novo item de inventário.
    """
    category: constr(min_length=3, max_length=50)
    name: constr(min_length=1, max_length=100)
    quantity: float
    unit: constr(min_length=1, max_length=10)
    price_unit: Optional[float] = 0.0

class FirearmCreate(BaseModel):
    """Validação para adição de novos equipamentos."""
    model: constr(min_length=2, max_length=100)
    serial: Optional[str]
    sigma: Optional[str]
    craf: Optional[str]

class ReloadSessionCreate(BaseModel):
    """Validação crítica para sessões de recarga (TEC-003)."""
    caliber: constr(min_length=2)
    quantity: int
    charge: Optional[float] = 0.0
    velocity_avg: Optional[float] = 0.0
    velocity_sd: Optional[float] = 0.0
    powder: Optional[str] = None
    projectile: Optional[str] = None
    primer: Optional[str] = None
    case: Optional[str] = None