"""Testes dos cartoes de DOPE salvos: CRUD e isolamento por usuario."""

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
    for mod in ("api.routers.auth", "api.routers.data", "api.routers.dope", "api.main"):
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


_CARD = {
    "name": ".308 168gr", "weight_grains": 168, "bc_g1": 0.462,
    "muzzle_velocity_fps": 2650, "zero_range_m": 100, "max_range_m": 800,
    "step_m": 100, "unit": "MIL", "click_value": 0.1,
}


class TestDopeCards:
    def test_crud_roundtrip(self, client):
        h = _auth(client)
        r = client.post("/api/dope-cards", headers=h, json=_CARD)
        assert r.status_code == 201
        cid = r.json()["id"]
        assert r.json()["name"] == ".308 168gr"
        assert len(client.get("/api/dope-cards", headers=h).json()) == 1
        r = client.put(f"/api/dope-cards/{cid}", headers=h, json={**_CARD, "max_range_m": 1000})
        assert r.json()["max_range_m"] == 1000
        assert client.delete(f"/api/dope-cards/{cid}", headers=h).status_code == 204
        assert client.get("/api/dope-cards", headers=h).json() == []

    def test_requires_auth(self, client):
        assert client.get("/api/dope-cards").status_code == 401
        assert client.post("/api/dope-cards", json=_CARD).status_code == 401

    def test_firearm_must_belong_to_user(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        gid = client.post("/api/firearms", headers=ha, json={"model": "Bergara"}).json()["id"]
        #  bob nao pode vincular a arma de alice.
        r = client.post("/api/dope-cards", headers=hb, json={**_CARD, "firearm_id": gid})
        assert r.status_code == 404

    def test_isolation(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        cid = client.post("/api/dope-cards", headers=ha, json=_CARD).json()["id"]
        assert client.get("/api/dope-cards", headers=hb).json() == []
        assert client.put(f"/api/dope-cards/{cid}", headers=hb, json=_CARD).status_code == 404
        assert client.delete(f"/api/dope-cards/{cid}", headers=hb).status_code == 404

    def test_links_to_firearm(self, client):
        h = _auth(client)
        gid = client.post("/api/firearms", headers=h, json={"model": "Tikka T3x"}).json()["id"]
        r = client.post("/api/dope-cards", headers=h, json={**_CARD, "firearm_id": gid})
        assert r.status_code == 201
        assert r.json()["firearm_id"] == gid
