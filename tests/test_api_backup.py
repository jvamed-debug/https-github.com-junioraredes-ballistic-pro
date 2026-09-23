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
        "api.routers.dope", "api.routers.backup", "api.main",
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


def _seed_and_export(client, h):
    """Cria dados variados (inclusive um DOPE vinculado a arma) e devolve o
    backup exportado, pronto para reimportar em outra conta."""
    fid = client.post("/api/firearms", headers=h,
                      json={"model": "Glock G25", "serial": "S1"}).json()["id"]
    client.post("/api/documents", headers=h, json={"title": "CR", "number": "CR-9"})
    client.post("/api/activities", headers=h, json={"category": "Pistola", "shots": 30})
    client.post("/api/events", headers=h, json={"title": "Copa", "date": "2027-01-01"})
    client.post("/api/places", headers=h, json={"name": "Clube X"})
    client.post("/api/dope-cards", headers=h, json={"name": "Receita 1", "firearm_id": fid})
    return client.get("/api/backup/export", headers=h).json()


class TestBackupImport:
    def test_requires_auth(self, client):
        assert client.post("/api/backup/import", json={"version": 1}).status_code == 401

    def test_rejects_wrong_version(self, client):
        h = _auth(client)
        r = client.post("/api/backup/import", headers=h, json={"version": 2})
        assert r.status_code == 400

    def test_roundtrip_into_fresh_account(self, client):
        backup = _seed_and_export(client, _auth(client, "alice"))

        hb = _auth(client, "bob")
        r = client.post("/api/backup/import", headers=hb, json=backup)
        assert r.status_code == 200
        body = r.json()
        assert body["total_imported"] == 6  # 1+1+1+1+1 + 1 dope
        assert body["imported"]["firearms"] == 1
        assert body["imported"]["dope_cards"] == 1

        #  Bob agora tem os dados; o export de Bob bate com o de Alice.
        bob = client.get("/api/backup/export", headers=hb).json()
        assert bob["counts"]["firearms"] == 1
        assert bob["firearms"][0]["serial"] == "S1"       # cifrado→claro→recifrado
        assert bob["documents"][0]["number"] == "CR-9"

    def test_dope_firearm_reference_is_remapped(self, client):
        backup = _seed_and_export(client, _auth(client, "alice"))
        hb = _auth(client, "bob")
        client.post("/api/backup/import", headers=hb, json=backup)

        guns = client.get("/api/firearms", headers=hb).json()
        cards = client.get("/api/dope-cards", headers=hb).json()
        #  O DOPE aponta para a arma recém-criada de Bob, não para o id de Alice.
        assert cards[0]["firearm_id"] == guns[0]["id"]

    def test_import_is_idempotent(self, client):
        backup = _seed_and_export(client, _auth(client, "alice"))
        hb = _auth(client, "bob")
        client.post("/api/backup/import", headers=hb, json=backup)

        r2 = client.post("/api/backup/import", headers=hb, json=backup)
        body = r2.json()
        assert body["total_imported"] == 0            # nada novo na 2ª vez
        assert sum(body["skipped"].values()) == 6
        #  Continua com uma cópia só de cada.
        assert client.get("/api/backup/export", headers=hb).json()["counts"]["firearms"] == 1

    def test_fills_only_empty_profile_fields(self, client):
        ha = _auth(client, "alice")
        client.put("/api/auth/me", headers=ha, json={"name": "Alice A", "cr_number": "CR-123"})
        backup = client.get("/api/backup/export", headers=ha).json()

        hb = _auth(client, "bob")
        client.put("/api/auth/me", headers=hb, json={"name": "Bob B"})  # name já preenchido
        r = client.post("/api/backup/import", headers=hb, json=backup)

        filled = r.json()["profile_filled"]
        assert "cr_number" in filled    # estava vazio → preenche
        assert "name" not in filled     # já tinha → preserva
        me = client.get("/api/auth/me", headers=hb).json()
        assert me["name"] == "Bob B" and me["cr_number"] == "CR-123"

    def test_isolation_import_only_affects_caller(self, client):
        backup = _seed_and_export(client, _auth(client, "alice"))
        hb = _auth(client, "bob")
        client.post("/api/backup/import", headers=hb, json=backup)
        #  Alice continua com exatamente o que tinha (não duplicou).
        ha2 = client.post("/api/auth/login", json={
            "username": "alice", "password": "senha1234"}).json()["access_token"]
        alice = client.get("/api/backup/export",
                          headers={"Authorization": f"Bearer {ha2}"}).json()
        assert alice["counts"]["firearms"] == 1
