"""Modelos de request/response da API de balistica.

Espelham as dataclasses do services.trajectory_service, mas como modelos
Pydantic — assim o FastAPI valida a entrada e publica um schema OpenAPI que o
frontend consome com tipos.
"""

from __future__ import annotations

from datetime import date
#  Alias para usar em campos cujo NOME e `date`: sob `from __future__ import
#  annotations`, um campo `date: Optional[date]` faz o proprio nome sombrear o
#  tipo, e o Pydantic resolve a anotacao para NoneType (o campo so aceitaria
#  None). Anotar com DateType evita o sombreamento.
from datetime import date as DateType
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class WeatherOut(BaseModel):
    temperature_c: float
    humidity_pct: float
    pressure_hpa: float
    altitude_m: float
    source: str


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
    #  Correcoes de tiro longo (opcionais). Sem latitude nao ha Coriolis; sem
    #  passo/SG nao ha deriva giroscopica.
    latitude_deg: Optional[float] = Field(None, ge=-90, le=90)
    azimuth_deg: float = Field(0.0, ge=0, le=360)
    twist_rate_in: float = Field(0.0, ge=0, le=30)
    twist_dir: Literal["right", "left"] = "right"
    bullet_length_in: float = Field(0.0, ge=0, le=3)
    stability: float = Field(0.0, ge=0, le=5)
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
    spin_drift_cm: float = 0.0


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
    spin_drift_cm: float = 0.0
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
    expiration: Optional[DateType] = None  # validade do CRAF
    collection: str = "pessoal"  # pessoal | clube
    gts: Optional[str] = None
    gts_expiration: Optional[DateType] = None
    craf_doc_url: Optional[str] = None
    gts_doc_url: Optional[str] = None

    @field_validator("collection")
    @classmethod
    def _collection_valida(cls, v: str) -> str:
        v = (v or "pessoal").strip().lower()
        if v not in ("pessoal", "clube"):
            raise ValueError("collection deve ser 'pessoal' ou 'clube'.")
        return v


class FirearmOut(FirearmIn):
    id: int
    image_url: Optional[str] = None


class FirearmAlert(BaseModel):
    """Um documento de arma vencido ou perto de vencer."""
    firearm_id: int
    model: str
    doc: str  # "CRAF" | "GTS"
    expiration: DateType
    days_left: int  # negativo = vencido
    collection: str


class DocumentIn(BaseModel):
    folder: str = Field("Geral", min_length=1, max_length=60)
    title: str = Field(..., min_length=1, max_length=120)
    number: Optional[str] = None
    issue_date: Optional[DateType] = None
    expiration: Optional[DateType] = None
    remind_days: int = Field(30, ge=0, le=365)
    file_url: Optional[str] = None
    notes: Optional[str] = None


class DocumentOut(DocumentIn):
    id: int
    has_file: bool = False
    file_name: Optional[str] = None


class DocumentUploadOut(DocumentOut):
    #  De onde vieram os campos: "ia", "heuristica" ou "vazio".
    extraction_source: str = "vazio"


class DocumentAlert(BaseModel):
    """Documento vencido ou dentro da antecedencia de lembrete."""
    document_id: int
    title: str
    folder: str
    expiration: DateType
    days_left: int  # negativo = vencido


class LogbookIn(BaseModel):
    caliber: str = Field(..., min_length=2)
    date: Optional[DateType] = None  # default: hoje, resolvido no endpoint
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
    date: DateType


class ActivityIn(BaseModel):
    date: Optional[DateType] = None  # default: hoje
    kind: str = Field("treino", pattern="^(treino|competicao)$")
    category: str = Field(..., min_length=1, max_length=40)
    caliber: Optional[str] = None
    firearm_id: Optional[int] = None
    shots: int = Field(0, ge=0)
    location: Optional[str] = None
    value: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class ActivityOut(ActivityIn):
    id: int
    date: DateType
    image_url: Optional[str] = None


class LevelOut(BaseModel):
    level: int
    title: str
    total_activities: int
    total_shots: int
    competitions: int
    categories: int          # combinacoes grupo+calibre distintas praticadas
    current_min: int         # limiar do nivel atual
    next_min: Optional[int]  # limiar do proximo nivel (None no ultimo)
    next_title: Optional[str]
    progress: float          # 0..1 rumo ao proximo nivel


class ActivitySummaryRow(BaseModel):
    category: str
    caliber: Optional[str] = None
    count: int
    shots: int
    last_date: Optional[date] = None


class ExpenseMonth(BaseModel):
    month: str  # "AAAA-MM"
    total: float


class ExpenseCategory(BaseModel):
    category: str
    total: float


class ExpenseReport(BaseModel):
    """Gastos das habitualidades no periodo: total, por mes e por categoria."""
    total: float
    count: int  # atividades com valor lancado
    by_month: list[ExpenseMonth]
    by_category: list[ExpenseCategory]


_EVENT_KINDS = {"competicao", "curso", "prova", "treino", "outro"}


class EventIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    date: DateType
    kind: str = "competicao"
    location: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("kind")
    @classmethod
    def _kind_valido(cls, v: str) -> str:
        v = (v or "competicao").strip().lower()
        if v not in _EVENT_KINDS:
            raise ValueError(f"kind deve ser um de {sorted(_EVENT_KINDS)}.")
        return v


class EventOut(EventIn):
    id: int


_PLACE_KINDS = {"clube", "loja", "estande", "outro"}


class PlaceIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    kind: str = "clube"
    address: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lng: Optional[float] = Field(None, ge=-180, le=180)
    phone: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("kind")
    @classmethod
    def _kind_valido(cls, v: str) -> str:
        v = (v or "clube").strip().lower()
        if v not in _PLACE_KINDS:
            raise ValueError(f"kind deve ser um de {sorted(_PLACE_KINDS)}.")
        return v


class PlaceOut(PlaceIn):
    id: int


class DopeCardIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    firearm_id: Optional[int] = None
    weight_grains: Optional[float] = Field(None, ge=0)
    bc_g1: Optional[float] = Field(None, ge=0)
    muzzle_velocity_fps: Optional[float] = Field(None, ge=0)
    diameter_mm: Optional[float] = Field(None, ge=0)
    bullet_length_in: Optional[float] = Field(None, ge=0)
    zero_range_m: Optional[float] = Field(None, ge=0)
    max_range_m: Optional[float] = Field(None, ge=0)
    step_m: Optional[float] = Field(None, ge=0)
    sight_height_cm: Optional[float] = Field(None, ge=0)
    twist_rate_in: Optional[float] = Field(None, ge=0)
    twist_dir: Optional[str] = None
    unit: Optional[str] = None
    click_value: Optional[float] = Field(None, ge=0)


class DopeCardOut(DopeCardIn):
    id: int


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
