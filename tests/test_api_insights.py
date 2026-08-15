"""Testes do painel de insights: agregacoes a partir do logbook e do estoque."""

import importlib

import pytest
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
    import services.reloading_service as rs
    importlib.reload(rs)
    for mod in ("api.routers.auth", "api.routers.data", "api.routers.insights", "api.main"):
        importlib.reload(importlib.import_module(mod))
    import api.main as main

    models.Base.metadata.create_all(models.engine)
    models.ensure_schema_compliance(models.engine)
    return TestClient(main.app)


def _auth(client, username="alice"):
    client.post("/api/auth/register", json={"username": username, "password": "senha1234"})
    tok = client.post("/api/auth/login", json={
        "username": username, "password": "senha1234",
    }).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _seed(client, h):
    client.post("/api/inventory", headers=h, json={
        "category": "Pólvora", "name": "CBC 216", "quantity": 500, "unit": "g", "price_unit": 0.5,
    })
    client.post("/api/inventory", headers=h, json={
        "category": "Espoleta", "name": "Small Pistol", "quantity": 30, "unit": "un", "price_unit": 0.2,
    })
    for g, sd, v in [(25, 8, 1180), (19, 6, 1195), (31, 12, 1160)]:
        client.post("/api/logbook", headers=h, json={
            "caliber": ".38 SPL", "quantity": 50, "powder": "CBC 216", "charge": 3.0,
            "primer": "Small Pistol", "velocity_avg": v, "velocity_sd": sd, "grouping_mm": g,
        })


class TestInsights:
    def test_requires_auth(self, client):
        assert client.get("/api/insights").status_code == 401

    def test_empty_is_zeroed(self, client):
        h = _auth(client)
        d = client.get("/api/insights", headers=h).json()
        assert d["totals"]["sessions"] == 0
        assert d["totals"]["best_group_mm"] is None
        assert d["best_by_group"] == []
        assert d["velocity_trend"] == []

    def test_totals_and_rankings(self, client):
        h = _auth(client)
        _seed(client, h)
        d = client.get("/api/insights", headers=h).json()
        t = d["totals"]
        assert t["sessions"] == 3
        assert t["rounds"] == 150
        assert t["best_group_mm"] == 19.0  # menor agrupamento
        assert t["avg_sd"] == pytest.approx(8.7, abs=0.1)
        assert t["inventory_value"] == 256.0  # 500*0.5 + 30*0.2
        assert t["low_stock_count"] == 1  # espoleta 30 <= 100
        #  Rankings ordenam do melhor (menor) para o pior.
        assert d["best_by_group"][0]["value"] == 19.0
        assert d["best_by_sd"][0]["value"] == 6.0
        assert len(d["velocity_trend"]) == 3

    def test_cost_trend_uses_inventory_pricing(self, client):
        h = _auth(client)
        _seed(client, h)
        d = client.get("/api/insights", headers=h).json()
        assert len(d["cost_trend"]) == 3
        assert all(c["unit_cost"] > 0 for c in d["cost_trend"])

    def test_isolated_by_user(self, client):
        ha = _auth(client, "alice")
        _seed(client, ha)
        hb = _auth(client, "bob")
        d = client.get("/api/insights", headers=hb).json()
        assert d["totals"]["sessions"] == 0
        assert d["totals"]["inventory_value"] == 0
