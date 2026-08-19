"""Testes do nivel do atirador (gamificacao a partir das habitualidades)."""

import importlib

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from api.routers.level import compute_level


class TestComputeLevel:
    def test_novato_at_zero(self):
        d = compute_level(0)
        assert d["level"] == 1 and d["title"] == "Novato" and d["progress"] == 0.0

    def test_progress_within_tier(self):
        d = compute_level(3)  # entre 0 e 5
        assert d["title"] == "Novato" and d["next_title"] == "Iniciante"
        assert d["progress"] == pytest.approx(0.6, abs=0.01)

    def test_tier_boundary_promotes(self):
        assert compute_level(5)["title"] == "Iniciante"
        assert compute_level(15)["title"] == "Praticante"

    def test_max_tier_has_no_next(self):
        d = compute_level(1000)
        assert d["title"] == "Mestre" and d["next_min"] is None and d["progress"] == 1.0


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
    for mod in ("api.routers.auth", "api.routers.activities", "api.routers.level", "api.main"):
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


class TestLevelEndpoint:
    def test_requires_auth(self, client):
        assert client.get("/api/level").status_code == 401

    def test_empty_is_novato(self, client):
        h = _auth(client)
        d = client.get("/api/level", headers=h).json()
        assert d["level"] == 1 and d["total_activities"] == 0

    def test_counts_and_isolation(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        for i in range(6):
            ha_body = {"category": "Pistola", "caliber": ".380", "shots": 50,
                       "kind": "competicao" if i == 0 else "treino"}
            client.post("/api/activities", headers=ha, json=ha_body)
        d = client.get("/api/level", headers=ha).json()
        assert d["total_activities"] == 6
        assert d["total_shots"] == 300
        assert d["competitions"] == 1
        assert d["categories"] == 1
        assert d["title"] == "Iniciante"  # 6 >= 5
        #  bob nao herda nada de alice.
        assert client.get("/api/level", headers=hb).json()["total_activities"] == 0
