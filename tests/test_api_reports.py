"""Testes dos endpoints de PDF (etiqueta da sessao e relatorio de acervo).

Verificam o essencial da camada HTTP: content-type application/pdf, corpo
comecando com o cabecalho %PDF, isolamento por usuario e exigencia de auth.
A formatacao dos PDFs em si tem cobertura em test_label_gen/test_report_gen.
"""

import importlib

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "api.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("JWT_SECRET", "test-secret")

    import core.models as models
    importlib.reload(models)
    import core.auth as auth
    importlib.reload(auth)
    import api.security as security
    importlib.reload(security)
    for mod in ("api.routers.auth", "api.routers.data", "api.routers.reports", "api.main"):
        importlib.reload(importlib.import_module(mod))
    import api.main as main

    models.Base.metadata.create_all(models.engine)
    models.ensure_schema_compliance(models.engine)
    return TestClient(main.app)


def _auth(client, username="alice"):
    client.post("/api/auth/register", json={
        "username": username, "password": "senha1234", "name": "Fulano de Tal",
    })
    tok = client.post("/api/auth/login", json={
        "username": username, "password": "senha1234",
    }).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _new_session(client, headers):
    return client.post("/api/logbook", headers=headers, json={
        "caliber": ".38 SPL", "quantity": 50, "powder": "CBC 216",
        "charge": 3.0, "primer": "Small Pistol",
    }).json()["id"]


class TestLabel:
    def test_returns_pdf(self, client):
        h = _auth(client)
        sid = _new_session(client, h)
        r = client.get(f"/api/logbook/{sid}/label", headers=h)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content[:5] == b"%PDF-"
        assert "attachment" in r.headers.get("content-disposition", "")

    def test_requires_auth(self, client):
        h = _auth(client)
        sid = _new_session(client, h)
        assert client.get(f"/api/logbook/{sid}/label").status_code == 401

    def test_isolated_by_user(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        sid = _new_session(client, ha)
        #  bob nao baixa a etiqueta de uma sessao de alice (404, nao vaza).
        assert client.get(f"/api/logbook/{sid}/label", headers=hb).status_code == 404

    def test_unknown_session_404(self, client):
        h = _auth(client)
        assert client.get("/api/logbook/999999/label", headers=h).status_code == 404


class TestInspectionReport:
    def test_returns_pdf_even_when_empty(self, client):
        h = _auth(client)
        r = client.get("/api/reports/inspection", headers=h)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content[:5] == b"%PDF-"

    def test_includes_data_and_requires_auth(self, client):
        h = _auth(client)
        client.post("/api/firearms", headers=h, json={"model": "Glock G17", "serial": "ABC123"})
        _new_session(client, h)
        r = client.get("/api/reports/inspection", headers=h)
        assert r.status_code == 200 and r.content[:5] == b"%PDF-"
        assert client.get("/api/reports/inspection").status_code == 401
