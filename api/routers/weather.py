"""Clima atual por coordenada, para preencher a atmosfera do calculo.

Autenticado (evita virar proxy aberto) e sem estado. Se a saida de rede
estiver bloqueada no ambiente, responde 502 e a UI cai no modo manual.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.schemas import WeatherOut
from api.security import get_current_user
from services.weather_service import WeatherError, fetch_weather

router = APIRouter(prefix="/api", tags=["clima"])


@router.get("/weather", response_model=WeatherOut)
def weather(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    current=Depends(get_current_user),
) -> WeatherOut:
    try:
        data = fetch_weather(lat, lon)
    except WeatherError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    return WeatherOut(**data)
