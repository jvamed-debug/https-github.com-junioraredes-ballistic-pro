"""Testes do consultor (IA) via API. Sem chave de LLM no ambiente, o advisor
opera em modo offline (por regras) — deterministico —, entao os testes
verificam esse caminho, que e o padrao de producao sem segredos."""

import importlib

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'api.db'}")
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    #  Garante o modo offline: sem chaves de LLM no ambiente de teste.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    import core.models as models
    importlib.reload(models)
    import core.auth as auth
    importlib.reload(auth)
    import api.security as security
    importlib.reload(security)
    for mod in ("api.routers.auth", "api.routers.advisor", "api.main"):
        importlib.reload(importlib.import_module(mod))
    import api.main as main

    models.Base.metadata.create_all(models.engine)
    models.ensure_schema_compliance(models.engine)
    return TestClient(main.app)


def _auth(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "senha1234"})
    tok = client.post("/api/auth/login", json={"username": "alice", "password": "senha1234"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_requires_auth(client):
    assert client.post("/api/advisor/load", json={"caliber": ".308"}).status_code == 401
    assert client.post("/api/advisor/trend", json={"sessions": []}).status_code == 401


def test_load_advice_offline(client):
    h = _auth(client)
    r = client.post("/api/advisor/load", headers=h, json={
        "caliber": ".308 WIN", "charge": 42.0, "velocity": 2650, "sd": 8, "grouping": 20,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "offline"
    #  SD de 8 fps deve ser avaliado como excelente consistencia.
    assert "EXCELENTE" in body["content"]
    assert ".308 WIN" in body["content"]


def test_load_advice_high_sd_warns(client):
    h = _auth(client)
    r = client.post("/api/advisor/load", headers=h, json={"caliber": "9mm", "sd": 35})
    assert "ELEVADO" in r.json()["content"]


def test_trend_needs_more_sessions(client):
    h = _auth(client)
    r = client.post("/api/advisor/trend", headers=h, json={"sessions": [{"velocity_avg": 2600}]})
    assert r.status_code == 200
    assert "Registre mais sess" in r.json()["content"]


def test_trend_detects_improvement(client):
    h = _auth(client)
    sessions = [
        {"velocity_avg": 2600, "velocity_sd": 12, "grouping_mm": 50},
        {"velocity_avg": 2605, "velocity_sd": 11, "grouping_mm": 45},
        {"velocity_avg": 2603, "velocity_sd": 10, "grouping_mm": 40},
        {"velocity_avg": 2602, "velocity_sd": 9, "grouping_mm": 30},
        {"velocity_avg": 2604, "velocity_sd": 10, "grouping_mm": 25},
        {"velocity_avg": 2601, "velocity_sd": 9, "grouping_mm": 20},
    ]
    r = client.post("/api/advisor/trend", headers=h, json={"sessions": sessions})
    assert r.status_code == 200
    assert "MELHORANDO" in r.json()["content"]
