"""Testes da exportação de backup (JSON com todos os dados do usuário)."""

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
    for mod in (
        "api.routers.auth", "api.routers.data", "api.routers.documents",
        "api.routers.activities", "api.routers.events", "api.routers.places",
        "api.routers.backup", "api.main",
    ):
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


class TestBackupExport:
    def test_requires_auth(self, client):
        assert client.get("/api/backup/export").status_code == 401

    def test_exports_all_sections_with_counts(self, client):
        h = _auth(client)
        client.post("/api/firearms", headers=h, json={"model": "Glock G25", "serial": "S1"})
        client.post("/api/documents", headers=h, json={"title": "CR", "number": "CR-9"})
        client.post("/api/activities", headers=h, json={"category": "Pistola", "shots": 30})
        client.post("/api/events", headers=h, json={"title": "Copa", "date": "2027-01-01"})
        client.post("/api/places", headers=h, json={"name": "Clube X"})

        r = client.get("/api/backup/export", headers=h)
        assert r.status_code == 200
        assert "attachment" in r.headers.get("content-disposition", "")
        body = r.json()
        assert body["version"] == 1 and body["exported_at"].endswith("Z")
        assert body["profile"]["username"] == "alice"
        assert body["counts"] == {
            "firearms": 1, "inventory": 0, "logbook": 0, "activities": 1,
            "documents": 1, "events": 1, "places": 1, "dope_cards": 0,
        }
        #  Campos cifrados saem em claro (backup útil fora do servidor).
        assert body["firearms"][0]["serial"] == "S1"
        assert body["documents"][0]["number"] == "CR-9"

    def test_excludes_file_bytes_and_user_id(self, client):
        h = _auth(client)
        pdf = b"%PDF-1.4 minimal"
        client.post("/api/documents/upload", headers=h,
                    files={"file": ("d.pdf", pdf, "application/pdf")})
        doc = client.get("/api/backup/export", headers=h).json()["documents"][0]
        assert "file_data" not in doc
        assert "user_id" not in doc
        #  O metadado do arquivo continua no backup.
        assert doc["file_name"] == "d.pdf"

    def test_isolation(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        client.post("/api/firearms", headers=ha, json={"model": "Só da Alice"})
        bob = client.get("/api/backup/export", headers=hb).json()
        assert bob["counts"]["firearms"] == 0
        assert bob["firearms"] == []
