"""Clima atual por coordenada, via Open-Meteo (sem chave, gratuito).

Fornece o que a calculadora de trajetoria pede: temperatura, umidade, pressao
reduzida ao nivel do mar (QNH) e altitude da estacao. Assim o atirador puxa a
atmosfera do local em vez de digitar na mao.

Depende de saida de rede para api.open-meteo.com. Se o ambiente nao permitir,
`fetch_weather` levanta WeatherError e a UI cai no preenchimento manual — que
continua funcionando como antes.
"""

from __future__ import annotations

import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_TIMEOUT_S = 6


class WeatherError(RuntimeError):
    """Falha ao obter o clima (rede indisponivel, resposta invalida etc.)."""


def fetch_weather(lat: float, lon: float) -> dict:
    """Clima atual em (lat, lon). Devolve o dict no formato da atmosfera do app.

    - temperature_c: temperatura a 2 m
    - humidity_pct: umidade relativa a 2 m
    - pressure_hpa: pressao reduzida ao nivel do mar (QNH) — o que o modelo
      espera; a queda ate a altitude entra por altitude_m
    - altitude_m: elevacao do ponto (para nao contar a altitude duas vezes)
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,pressure_msl,surface_pressure",
    }
    try:
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=_TIMEOUT_S)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        raise WeatherError(f"Nao foi possivel consultar o clima: {exc}") from exc
    except ValueError as exc:  # JSON invalido
        raise WeatherError("Resposta de clima invalida.") from exc

    current = data.get("current") or {}
    temp = current.get("temperature_2m")
    humidity = current.get("relative_humidity_2m")
    #  Prefere a QNH (nivel do mar) + elevacao. Sem ela, usa a pressao da
    #  estacao e zera a altitude para nao descontar a altitude duas vezes.
    pressure_msl = current.get("pressure_msl")
    surface = current.get("surface_pressure")
    elevation = data.get("elevation")

    if temp is None or (pressure_msl is None and surface is None):
        raise WeatherError("Clima sem os campos necessarios.")

    if pressure_msl is not None:
        pressure_hpa = pressure_msl
        altitude_m = elevation if elevation is not None else 0.0
    else:
        pressure_hpa = surface
        altitude_m = 0.0

    return {
        "temperature_c": round(float(temp), 1),
        "humidity_pct": round(float(humidity), 0) if humidity is not None else 50.0,
        "pressure_hpa": round(float(pressure_hpa), 1),
        "altitude_m": round(float(altitude_m), 0),
        "source": "open-meteo",
    }
