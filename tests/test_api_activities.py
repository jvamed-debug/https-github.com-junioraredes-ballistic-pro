"""Testes das habitualidades/competicoes: CRUD, resumo por grupo+calibre e
isolamento por usuario."""

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
    for mod in ("api.routers.auth", "api.routers.data", "api.routers.activities", "api.main"):
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
    for cat, cal, sh in [("Pistola", ".380", 50), ("Pistola", ".380", 30), ("Revólver", ".38 SPL", 24)]:
        client.post("/api/activities", headers=h, json={
            "category": cat, "caliber": cal, "shots": sh, "kind": "treino",
        })


class TestActivities:
    def test_requires_auth(self, client):
        assert client.get("/api/activities").status_code == 401
        assert client.post("/api/activities", json={"category": "Pistola"}).status_code == 401

    def test_crud_and_defaults_date(self, client):
        h = _auth(client)
        r = client.post("/api/activities", headers=h, json={"category": "Pistola", "caliber": ".380", "shots": 50})
        assert r.status_code == 201
        body = r.json()
        assert body["date"] and body["kind"] == "treino"
        aid = body["id"]
        assert len(client.get("/api/activities", headers=h).json()) == 1
        r = client.put(f"/api/activities/{aid}", headers=h, json={"category": "Pistola", "caliber": ".380", "shots": 75, "kind": "competicao"})
        assert r.json()["shots"] == 75 and r.json()["kind"] == "competicao"
        assert client.delete(f"/api/activities/{aid}", headers=h).status_code == 204

    def test_kind_is_validated(self, client):
        h = _auth(client)
        assert client.post("/api/activities", headers=h, json={"category": "Pistola", "kind": "xpto"}).status_code == 422

    def test_summary_counts_per_group_and_caliber(self, client):
        h = _auth(client)
        _seed(client, h)
        rows = client.get("/api/activities/summary", headers=h).json()
        by = {(r["category"], r["caliber"]): r for r in rows}
        assert by[("Pistola", ".380")]["count"] == 2
        assert by[("Pistola", ".380")]["shots"] == 80
        assert by[("Revólver", ".38 SPL")]["count"] == 1

    def test_summary_since_filters(self, client):
        h = _auth(client)
        client.post("/api/activities", headers=h, json={"category": "Pistola", "date": "2020-01-01", "shots": 10})
        client.post("/api/activities", headers=h, json={"category": "Pistola", "date": "2026-06-01", "shots": 20})
        rows = client.get("/api/activities/summary", headers=h, params={"since": "2026-01-01"}).json()
        assert len(rows) == 1 and rows[0]["count"] == 1 and rows[0]["shots"] == 20

    def test_firearm_must_belong_to_user(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        gid = client.post("/api/firearms", headers=ha, json={"model": "Glock"}).json()["id"]
        r = client.post("/api/activities", headers=hb, json={"category": "Pistola", "firearm_id": gid})
        assert r.status_code == 404

    def test_isolation(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        _seed(client, ha)
        assert client.get("/api/activities", headers=hb).json() == []
        assert client.get("/api/activities/summary", headers=hb).json() == []


class TestExpenses:
    def test_requires_auth(self, client):
        assert client.get("/api/activities/expenses").status_code == 401

    def test_aggregates_by_month_and_category(self, client):
        h = _auth(client)
        for cat, d, val in [
            ("Pistola", "2026-01-10", 100.0),
            ("Pistola", "2026-01-20", 50.0),
            ("Carabina", "2026-02-05", 200.0),
            ("Revólver", "2026-02-15", None),  # sem valor -> ignorado
        ]:
            body = {"category": cat, "date": d}
            if val is not None:
                body["value"] = val
            client.post("/api/activities", headers=h, json=body)
        rep = client.get("/api/activities/expenses", headers=h).json()
        assert rep["total"] == 350.0
        assert rep["count"] == 3
        assert rep["by_month"] == [
            {"month": "2026-01", "total": 150.0},
            {"month": "2026-02", "total": 200.0},
        ]
        # Categorias ordenadas por gasto (maior primeiro).
        assert rep["by_category"][0] == {"category": "Carabina", "total": 200.0}
        assert {"category": "Pistola", "total": 150.0} in rep["by_category"]

    def test_period_filter(self, client):
        h = _auth(client)
        client.post("/api/activities", headers=h, json={
            "category": "Pistola", "date": "2026-01-10", "value": 100.0,
        })
        client.post("/api/activities", headers=h, json={
            "category": "Pistola", "date": "2026-03-10", "value": 80.0,
        })
        rep = client.get("/api/activities/expenses?since=2026-02-01", headers=h).json()
        assert rep["total"] == 80.0 and rep["count"] == 1
        rep2 = client.get(
            "/api/activities/expenses?since=2026-01-01&until=2026-02-01", headers=h,
        ).json()
        assert rep2["total"] == 100.0

    def test_empty_and_isolation(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        client.post("/api/activities", headers=ha, json={
            "category": "Pistola", "value": 100.0,
        })
        assert client.get("/api/activities/expenses", headers=hb).json() == {
            "total": 0.0, "count": 0, "by_month": [], "by_category": [],
        }
