"""Testes da lista de locais (clubes, lojas e estandes)."""

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
    for mod in ("api.routers.auth", "api.routers.places", "api.main"):
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


class TestPlaces:
    def test_requires_auth(self, client):
        assert client.get("/api/places").status_code == 401

    def test_crud_roundtrip(self, client):
        h = _auth(client)
        r = client.post("/api/places", headers=h, json={
            "name": "Clube de Tiro X", "kind": "Clube", "city": "Curitiba",
            "lat": -25.43, "lng": -49.27,
        })
        assert r.status_code == 201
        body = r.json()
        assert body["kind"] == "clube"  # normalizado
        assert body["lat"] == -25.43
        pid = body["id"]
        upd = client.put(f"/api/places/{pid}", headers=h, json={
            "name": "Clube de Tiro X", "kind": "clube", "phone": "4133334444",
        })
        assert upd.json()["phone"] == "4133334444"
        assert client.delete(f"/api/places/{pid}", headers=h).status_code == 204
        assert client.get("/api/places", headers=h).json() == []

    def test_name_required_and_kind_and_coords_validated(self, client):
        h = _auth(client)
        assert client.post("/api/places", headers=h, json={"kind": "clube"}).status_code == 422
        assert client.post("/api/places", headers=h,
                           json={"name": "X", "kind": "bar"}).status_code == 422
        assert client.post("/api/places", headers=h,
                           json={"name": "X", "lat": 200}).status_code == 422

    def test_ordered_by_kind_then_name(self, client):
        h = _auth(client)
        client.post("/api/places", headers=h, json={"name": "Zulu", "kind": "loja"})
        client.post("/api/places", headers=h, json={"name": "Alfa", "kind": "clube"})
        client.post("/api/places", headers=h, json={"name": "Bravo", "kind": "clube"})
        names = [p["name"] for p in client.get("/api/places", headers=h).json()]
        assert names == ["Alfa", "Bravo", "Zulu"]

    def test_isolation(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        pid = client.post("/api/places", headers=ha, json={"name": "Meu"}).json()["id"]
        assert client.get("/api/places", headers=hb).json() == []
        assert client.put(f"/api/places/{pid}", headers=hb,
                          json={"name": "hack"}).status_code == 404
        assert client.delete(f"/api/places/{pid}", headers=hb).status_code == 404
