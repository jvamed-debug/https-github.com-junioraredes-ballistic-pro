"""Endpoints de balistica: catalogo de recarga e calculo de trajetoria/DOPE.

Sao stateless e reusam services/ puros — nao tocam banco nem autenticacao, o
que os torna a fatia mais segura para abrir a API e comecar o frontend.
"""

from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from api.schemas import (
    ProjectileIn,
    TrajectoryRequest,
    TrajectoryResponse,
)
from services.ballistics_service import BallisticsService
from services.trajectory_service import (
    AtmosphericConditions,
    ProjectileData,
    build_dope_card,
    calculate_trajectory,
)

router = APIRouter(prefix="/api", tags=["ballistics"])


@router.get("/catalog/calibers")
def list_calibers() -> list[str]:
    """Nomes dos calibres do catalogo CBC."""
    return BallisticsService.get_calibers()


@router.get("/catalog")
def full_catalog() -> dict:
    """Catalogo completo (calibres -> projeteis -> polvoras) e metadados."""
    return BallisticsService.load_data()


@router.get("/catalog/caliber/{name}")
def caliber_details(name: str) -> dict:
    details = BallisticsService.get_caliber_details(name)
    if not details:
        raise HTTPException(status_code=404, detail="Calibre nao encontrado.")
    return details


def _to_projectile(p: ProjectileIn) -> ProjectileData:
    return ProjectileData(
        weight_grains=p.weight_grains,
        bc_g1=p.bc_g1,
        bc_g7=p.bc_g7,
        diameter_mm=p.diameter_mm,
        muzzle_velocity_fps=p.muzzle_velocity_fps,
    )


@router.post("/trajectory", response_model=TrajectoryResponse)
def trajectory(req: TrajectoryRequest) -> TrajectoryResponse:
    """Calcula a trajetoria externa e, se `dope` vier no corpo, ja devolve o
    cartao de DOPE (correcao de torre em cliques + compensacao de angulo)."""
    if req.max_range_m < req.zero_range_m:
        raise HTTPException(
            status_code=422,
            detail="max_range_m deve ser maior ou igual a zero_range_m.",
        )

    atmosphere = AtmosphericConditions(
        temperature_c=req.atmosphere.temperature_c,
        pressure_hpa=req.atmosphere.pressure_hpa,
        humidity_pct=req.atmosphere.humidity_pct,
        altitude_m=req.atmosphere.altitude_m,
    )
    result = calculate_trajectory(
        projectile=_to_projectile(req.projectile),
        zero_range_m=req.zero_range_m,
        max_range_m=req.max_range_m,
        step_m=req.step_m,
        sight_height_cm=req.sight_height_cm,
        wind_speed_ms=req.wind_speed_ms,
        wind_angle_deg=req.wind_angle_deg,
        atmosphere=atmosphere,
    )
    if not result.points:
        raise HTTPException(
            status_code=422,
            detail="Nao foi possivel calcular a trajetoria com esses parametros.",
        )

    dope_card = None
    if req.dope is not None:
        dope_card = [
            asdict(e)
            for e in build_dope_card(
                result,
                unit=req.dope.unit,
                click_value=req.dope.click_value,
                incline_deg=req.dope.incline_deg,
            )
        ]

    return TrajectoryResponse(
        zero_range_m=result.zero_range_m,
        max_point_blank_range_m=result.max_point_blank_range_m,
        summary=result.summary,
        points=[asdict(p) for p in result.points],
        dope_card=dope_card,
    )
