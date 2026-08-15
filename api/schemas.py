"""Modelos de request/response da API de balistica.

Espelham as dataclasses do services.trajectory_service, mas como modelos
Pydantic — assim o FastAPI valida a entrada e publica um schema OpenAPI que o
frontend consome com tipos.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class AtmosphereIn(BaseModel):
    temperature_c: float = Field(15.0, ge=-40, le=60)
    pressure_hpa: float = Field(1013.25, ge=800, le=1100)
    humidity_pct: float = Field(50.0, ge=0, le=100)
    altitude_m: float = Field(0.0, ge=0, le=6000)


class ProjectileIn(BaseModel):
    weight_grains: float = Field(..., gt=0, le=1000)
    #  Um BC so vale com a curva de arrasto a que foi medido. O G7 tem
    #  prioridade quando informado (projetil boat-tail moderno).
    bc_g1: float = Field(0.0, ge=0, le=1.5)
    bc_g7: float = Field(0.0, ge=0, le=1.5)
    diameter_mm: float = Field(0.0, ge=0, le=30)
    muzzle_velocity_fps: float = Field(..., gt=0, le=5000)


class DopeIn(BaseModel):
    """Parametros da torre para gerar o cartao de DOPE junto da trajetoria."""

    unit: Literal["MIL", "MOA"] = "MIL"
    click_value: float = Field(0.1, gt=0, le=2)
    incline_deg: float = Field(0.0, ge=-90, le=90)


class TrajectoryRequest(BaseModel):
    projectile: ProjectileIn
    zero_range_m: float = Field(100.0, gt=0, le=2000)
    max_range_m: float = Field(500.0, gt=0, le=3000)
    step_m: float = Field(25.0, gt=0, le=500)
    sight_height_cm: float = Field(4.0, ge=0, le=30)
    wind_speed_ms: float = Field(0.0, ge=0, le=60)
    wind_angle_deg: float = Field(90.0, ge=0, le=360)
    atmosphere: AtmosphereIn = Field(default_factory=AtmosphereIn)
    #  Quando presente, a resposta ja traz o cartao de DOPE calculado.
    dope: Optional[DopeIn] = None


class TrajectoryPointOut(BaseModel):
    range_m: float
    drop_cm: float
    drop_moa: float
    drop_mil: float
    velocity_ms: float
    velocity_fps: float
    energy_j: float
    energy_ftlbs: float
    time_of_flight_s: float
    wind_drift_cm: float
    wind_drift_moa: float


class DopeEntryOut(BaseModel):
    range_m: float
    unit: str
    elevation: float
    elevation_clicks: int
    windage: float
    windage_dir: str
    windage_clicks: int
    drop_cm: float
    wind_drift_cm: float
    velocity_fps: float
    energy_ftlbs: float
    time_of_flight_s: float


class TrajectoryResponse(BaseModel):
    zero_range_m: float
    max_point_blank_range_m: float
    summary: dict
    points: list[TrajectoryPointOut]
    dope_card: Optional[list[DopeEntryOut]] = None


# ---------------------------------------------------------------------------
# Autenticacao e usuario
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    name: Optional[str] = None
    cpf: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class RecoverRequest(BaseModel):
    identifier: str = Field(..., description="E-mail ou telefone cadastrado.")


# WebAuthn / passkeys (login por biometria) ---------------------------------


class WebAuthnAvailable(BaseModel):
    available: bool


class WebAuthnLoginBegin(BaseModel):
    username: str = Field(..., min_length=1)


class WebAuthnLoginComplete(BaseModel):
    username: str = Field(..., min_length=1)
    #  Resposta crua de navigator.credentials.get() serializada pelo browser.
    credential: dict


class WebAuthnRegisterComplete(BaseModel):
    #  Resposta crua de navigator.credentials.create().
    credential: dict
    label: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    detail: str


class UserOut(BaseModel):
    id: int
    username: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    cpf: Optional[str] = None
    cr_number: Optional[str] = None
    cr_expiration: Optional[date] = None
    address_acervo: Optional[str] = None
    is_premium: bool = False


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    cpf: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    cr_number: Optional[str] = None
    cr_expiration: Optional[date] = None
    address_acervo: Optional[str] = None


# ---------------------------------------------------------------------------
# Dados do usuario: inventario, armas e logbook (todos no escopo do usuario)
# ---------------------------------------------------------------------------


class InventoryIn(BaseModel):
    category: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    quantity: float = Field(0.0, ge=0)
    unit: str = Field(..., min_length=1, max_length=10)
    price_unit: float = Field(0.0, ge=0)
    batch_number: Optional[str] = None
    expiration_date: Optional[date] = None


class InventoryOut(InventoryIn):
    id: int


class FirearmIn(BaseModel):
    model: str = Field(..., min_length=2, max_length=100)
    serial: Optional[str] = None
    sigma: Optional[str] = None
    craf: Optional[str] = None
    expiration: Optional[date] = None


class FirearmOut(FirearmIn):
    id: int
    image_url: Optional[str] = None


class LogbookIn(BaseModel):
    caliber: str = Field(..., min_length=2)
    date: Optional[date] = None  # default: hoje, resolvido no endpoint
    quantity: int = Field(1, ge=1)
    projectile: Optional[str] = None
    powder: Optional[str] = None
    charge: Optional[float] = Field(None, ge=0)
    primer: Optional[str] = None
    case: Optional[str] = None
    velocity_avg: Optional[float] = Field(None, ge=0)
    velocity_sd: Optional[float] = Field(None, ge=0)
    grouping_mm: Optional[float] = Field(None, ge=0)
    firearm_id: Optional[int] = None
    notes: Optional[str] = None


class LogbookOut(LogbookIn):
    id: int
    date: date


class LogbookCreateOut(LogbookOut):
    #  Preenchidos so quando o POST pede deducao de estoque (deduct=true).
    #  deductions = linhas do que saiu (ou faltou) do inventario; unit_cost =
    #  custo estimado por municao com base no preco de estoque atual.
    deductions: list[str] = Field(default_factory=list)
    unit_cost: Optional[float] = None


# ---------------------------------------------------------------------------
# Consultor (IA) — modo offline por regras; usa LLM se houver chave no ambiente
# ---------------------------------------------------------------------------


class LoadAdviceIn(BaseModel):
    caliber: str = Field(..., min_length=1)
    projectile: Optional[str] = None
    powder: Optional[str] = None
    charge: Optional[float] = None
    velocity: Optional[float] = None
    sd: Optional[float] = None
    grouping: Optional[float] = None


class TrendSessionIn(BaseModel):
    velocity_avg: Optional[float] = None
    velocity_sd: Optional[float] = None
    grouping_mm: Optional[float] = None


class TrendAdviceIn(BaseModel):
    sessions: list[TrendSessionIn] = Field(default_factory=list)


class AdviceOut(BaseModel):
    content: str
    provider: str
    confidence: str


# ---------------------------------------------------------------------------
# Dados de recarga: avisos de seguranca e estimador de carga
# ---------------------------------------------------------------------------


class ReloadWarning(BaseModel):
    #  "erro" = bloqueante (troca de serie, procedencia sem confirmar); "aviso"
    #  = cautela. Mesmo vocabulario do app Streamlit (components/logbook_inventory).
    severity: Literal["erro", "aviso"]
    message: str


class ReloadWarningsOut(BaseModel):
    caliber: Optional[str] = None
    powder: Optional[str] = None
    warnings: list[ReloadWarning] = Field(default_factory=list)


class ChargeEstimateIn(BaseModel):
    projectile_grains: float = Field(..., gt=0, le=1000)
    velocity_fps: float = Field(..., gt=0, le=5000)
    #  Poder calorifico da polvora, em J/g. Faixa tipica 3800–4200 J/g.
    calorific_j_per_g: float = Field(4000.0, gt=0, le=10000)
    #  Fracao da energia quimica que vira energia cinetica do projetil.
    efficiency_percent: float = Field(30.0, gt=0, le=100)


class ChargeEstimateOut(BaseModel):
    energy_j: float
    energy_ftlbs: float
    estimated_charge_grains: float
