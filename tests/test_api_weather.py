"""Testes do endpoint de clima (Open-Meteo). A chamada HTTP e simulada — nao
tocamos a rede — para cobrir o mapeamento e os caminhos de erro."""

import importlib

import pytest
import requests
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("JWT_SECRET", "test-secret")

    import core.models as models
    importlib.reload(models)
    import core.auth as auth
    importlib.reload(auth)
    import api.security as security
    importlib.reload(security)
    import services.weather_service as ws
    importlib.reload(ws)
    for mod in ("api.routers.auth", "api.routers.weather", "api.main"):
        importlib.reload(importlib.import_module(mod))
    import api.main as main

    models.Base.metadata.create_all(models.engine)
    models.ensure_schema_compliance(models.engine)
    return TestClient(main.app)


def _auth(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "senha1234"})
    tok = client.post("/api/auth/login", json={
        "username": "alice", "password": "senha1234",
    }).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


class _FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")

    def json(self):
        return self._payload


_SAMPLE = {
    "elevation": 760.0,
    "current": {
        "temperature_2m": 24.3,
        "relative_humidity_2m": 55,
        "pressure_msl": 1015.4,
        "surface_pressure": 927.1,
    },
}


def test_maps_open_meteo_to_atmosphere(client, monkeypatch):
    import services.weather_service as ws
    monkeypatch.setattr(ws.requests, "get", lambda *a, **k: _FakeResp(_SAMPLE))
    h = _auth(client)
    r = client.get("/api/weather", params={"lat": -23.5, "lon": -46.6}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["temperature_c"] == 24.3
    assert body["humidity_pct"] == 55
    assert body["pressure_hpa"] == 1015.4  # QNH (nivel do mar)
    assert body["altitude_m"] == 760  # elevacao
    assert body["source"] == "open-meteo"


def test_network_failure_is_502(client, monkeypatch):
    import services.weather_service as ws

    def _boom(*a, **k):
        raise requests.ConnectionError("sem rede")

    monkeypatch.setattr(ws.requests, "get", _boom)
    h = _auth(client)
    r = client.get("/api/weather", params={"lat": 0, "lon": 0}, headers=h)
    assert r.status_code == 502


def test_requires_auth(client):
    assert client.get("/api/weather", params={"lat": 0, "lon": 0}).status_code == 401


def test_rejects_out_of_range_coords(client):
    h = _auth(client)
    assert client.get("/api/weather", params={"lat": 200, "lon": 0}, headers=h).status_code == 422
