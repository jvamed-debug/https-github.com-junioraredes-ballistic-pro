"""Testes da agenda de eventos e competicoes."""

import importlib
from datetime import date, timedelta

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
    for mod in ("api.routers.auth", "api.routers.events", "api.main"):
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


class TestEvents:
    def test_requires_auth(self, client):
        assert client.get("/api/events").status_code == 401

    def test_crud_roundtrip(self, client):
        h = _auth(client)
        r = client.post("/api/events", headers=h, json={
            "title": "Copa Brasil", "date": "2026-09-10", "kind": "Competicao",
            "location": "Clube X",
        })
        assert r.status_code == 201
        body = r.json()
        assert body["kind"] == "competicao"  # normalizado
        did = body["id"]
        upd = client.put(f"/api/events/{did}", headers=h, json={
            "title": "Copa Brasil - Etapa 2", "date": "2026-09-11",
        })
        assert upd.json()["title"] == "Copa Brasil - Etapa 2"
        assert client.delete(f"/api/events/{did}", headers=h).status_code == 204
        assert client.get("/api/events", headers=h).json() == []

    def test_date_required_and_kind_validated(self, client):
        h = _auth(client)
        assert client.post("/api/events", headers=h,
                           json={"title": "Sem data"}).status_code == 422
        assert client.post("/api/events", headers=h,
                           json={"title": "X", "date": "2026-01-01", "kind": "festa"}).status_code == 422

    def test_ordered_by_date_and_upcoming_filter(self, client):
        h = _auth(client)
        today = date.today()
        client.post("/api/events", headers=h, json={
            "title": "Passado", "date": str(today - timedelta(days=5)),
        })
        client.post("/api/events", headers=h, json={
            "title": "Futuro B", "date": str(today + timedelta(days=30)),
        })
        client.post("/api/events", headers=h, json={
            "title": "Futuro A", "date": str(today + timedelta(days=2)),
        })
        allrows = client.get("/api/events", headers=h).json()
        assert [e["title"] for e in allrows] == ["Passado", "Futuro A", "Futuro B"]
        upcoming = client.get("/api/events?upcoming=true", headers=h).json()
        assert [e["title"] for e in upcoming] == ["Futuro A", "Futuro B"]

    def test_isolation(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        did = client.post("/api/events", headers=ha, json={
            "title": "Meu", "date": "2026-05-01",
        }).json()["id"]
        assert client.get("/api/events", headers=hb).json() == []
        assert client.put(f"/api/events/{did}", headers=hb,
                          json={"title": "hack", "date": "2026-05-01"}).status_code == 404
        assert client.delete(f"/api/events/{did}", headers=hb).status_code == 404
