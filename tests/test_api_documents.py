"""Testes dos documentos do CAC (pastas, validade e lembretes)."""

import importlib
import io
from datetime import date, timedelta

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient


def _pdf(lines: list[str]) -> bytes:
    """Gera um PDF simples com texto selecionavel (para a leitura heuristica)."""
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 800
    for line in lines:
        c.drawString(50, y, line)
        y -= 20
    c.save()
    return buf.getvalue()


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


class TestHeuristicParser:
    def test_identifies_craf_number_and_expiration(self):
        from services.doc_extraction import parse_text_heuristic
        r = parse_text_heuristic(
            "CERTIFICADO DE REGISTRO DE ARMA DE FOGO (CRAF)\n"
            "Número: 1234567\nEmissão: 10/05/2022\nValidade: 09/05/2032\n"
        )
        assert r["title"] == "CRAF"
        assert r["folder"] == "Registro"
        assert r["number"] == "1234567"
        assert r["expiration"] == "2032-05-09"
        assert r["issue_date"] == "2022-05-10"
        assert r["source"] == "heuristica"

    def test_empty_text_marks_source_vazio(self):
        from services.doc_extraction import parse_text_heuristic
        assert parse_text_heuristic("")["source"] == "vazio"

    def test_unlabeled_dates_pick_latest_as_expiration(self):
        from services.doc_extraction import parse_text_heuristic
        r = parse_text_heuristic("Documento qualquer\n01/01/2020\n31/12/2030\n")
        assert r["expiration"] == "2030-12-31"
        assert r["issue_date"] == "2020-01-01"


class TestUploadAndDownload:
    def test_upload_reads_fields_stores_file_and_downloads(self, client):
        h = _auth(client)
        pdf = _pdf([
            "GUIA DE TRAFEGO",
            "Numero: GT-2024-987",
            "Validade: 15/08/2028",
        ])
        r = client.post("/api/documents/upload", headers=h,
                        files={"file": ("gt.pdf", pdf, "application/pdf")})
        assert r.status_code == 201
        body = r.json()
        assert body["has_file"] is True
        assert body["file_name"] == "gt.pdf"
        assert body["folder"] == "Transporte"
        assert body["expiration"] == "2028-08-15"
        assert body["extraction_source"] == "heuristica"

        did = body["id"]
        #  aparece na listagem com flag de arquivo (sem os bytes).
        listed = client.get("/api/documents", headers=h).json()
        assert listed[0]["has_file"] is True and "file_data" not in listed[0]

        #  download devolve o mesmo PDF.
        dl = client.get(f"/api/documents/{did}/file", headers=h)
        assert dl.status_code == 200
        assert dl.headers["content-type"].startswith("application/pdf")
        assert dl.content == pdf

    def test_upload_rejects_non_pdf(self, client):
        h = _auth(client)
        r = client.post("/api/documents/upload", headers=h,
                        files={"file": ("nota.txt", b"oi", "text/plain")})
        assert r.status_code == 400

    def test_download_requires_auth_and_isolation(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        pdf = _pdf(["CR", "Validade: 01/01/2030"])
        did = client.post("/api/documents/upload", headers=ha,
                          files={"file": ("cr.pdf", pdf, "application/pdf")}).json()["id"]
        assert client.get(f"/api/documents/{did}/file").status_code == 401
        assert client.get(f"/api/documents/{did}/file", headers=hb).status_code == 404

    def test_download_404_when_no_file(self, client):
        h = _auth(client)
        did = client.post("/api/documents", headers=h, json={"title": "Sem arquivo"}).json()["id"]
        assert client.get(f"/api/documents/{did}/file", headers=h).status_code == 404
