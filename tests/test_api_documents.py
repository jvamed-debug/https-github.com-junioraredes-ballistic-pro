"""Testes dos documentos do CAC (pastas, validade e lembretes)."""

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
    for mod in ("api.routers.auth", "api.routers.documents", "api.main"):
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


class TestDocumentsCrud:
    def test_requires_auth(self, client):
        assert client.get("/api/documents").status_code == 401

    def test_crud_roundtrip_and_defaults(self, client):
        h = _auth(client)
        r = client.post("/api/documents", headers=h, json={
            "title": "CR", "number": "CR-123", "folder": "Registro",
        })
        assert r.status_code == 201
        body = r.json()
        assert body["number"] == "CR-123"  # cifrado no banco, claro na resposta
        assert body["folder"] == "Registro"
        assert body["remind_days"] == 30   # default

        did = body["id"]
        upd = client.put(f"/api/documents/{did}", headers=h, json={
            "title": "CR renovado", "folder": "Registro", "remind_days": 60,
        })
        assert upd.json()["title"] == "CR renovado" and upd.json()["remind_days"] == 60

        assert client.delete(f"/api/documents/{did}", headers=h).status_code == 204
        assert client.get("/api/documents", headers=h).json() == []

    def test_title_required(self, client):
        h = _auth(client)
        assert client.post("/api/documents", headers=h, json={"folder": "X"}).status_code == 422

    def test_remind_days_out_of_range_rejected(self, client):
        h = _auth(client)
        assert client.post("/api/documents", headers=h, json={
            "title": "X", "remind_days": 999,
        }).status_code == 422

    def test_isolation(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        did = client.post("/api/documents", headers=ha, json={"title": "Meu"}).json()["id"]
        assert client.get("/api/documents", headers=hb).json() == []
        assert client.put(f"/api/documents/{did}", headers=hb,
                          json={"title": "hack"}).status_code == 404
        assert client.delete(f"/api/documents/{did}", headers=hb).status_code == 404


class TestDocumentAlerts:
    def test_requires_auth(self, client):
        assert client.get("/api/documents/alerts").status_code == 401

    def test_reminder_window_per_document(self, client):
        h = _auth(client)
        today = date.today()
        # Vence em 20 dias, lembrete 30 -> alerta.
        client.post("/api/documents", headers=h, json={
            "title": "Perto", "expiration": str(today + timedelta(days=20)), "remind_days": 30,
        })
        # Vence em 20 dias, lembrete 7 -> ainda nao alerta.
        client.post("/api/documents", headers=h, json={
            "title": "Longe", "expiration": str(today + timedelta(days=20)), "remind_days": 7,
        })
        # Ja vencido -> alerta (days_left negativo).
        client.post("/api/documents", headers=h, json={
            "title": "Vencido", "expiration": str(today - timedelta(days=3)), "remind_days": 10,
        })
        # Sem validade -> nunca alerta.
        client.post("/api/documents", headers=h, json={"title": "Sem data"})

        alerts = client.get("/api/documents/alerts", headers=h).json()
        titles = [a["title"] for a in alerts]
        assert titles == ["Vencido", "Perto"]  # ordenado por days_left
        assert alerts[0]["days_left"] == -3

    def test_alerts_isolated(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        client.post("/api/documents", headers=ha, json={
            "title": "A", "expiration": str(date.today()), "remind_days": 5,
        })
        assert len(client.get("/api/documents/alerts", headers=ha).json()) == 1
        assert client.get("/api/documents/alerts", headers=hb).json() == []
