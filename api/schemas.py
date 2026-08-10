"""Modelos de request/response da API de balistica.

Espelham as dataclasses do services.trajectory_service, mas como modelos
Pydantic — assim o FastAPI valida a entrada e publica um schema OpenAPI que o
frontend consome com tipos.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


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
