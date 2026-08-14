"""Testes dos endpoints de dados do usuario (inventario, armas, logbook).

Rodam em MODO PRODUCAO (FERNET_KEY ligada) e verificam sobretudo o ISOLAMENTO
por usuario: um usuario nunca ve nem altera o registro de outro.
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
    for mod in ("api.routers.auth", "api.routers.ballistics", "api.routers.data", "api.main"):
        importlib.reload(importlib.import_module(mod))
    import api.main as main

    models.Base.metadata.create_all(models.engine)
    models.ensure_schema_compliance(models.engine)
    return TestClient(main.app)


def _auth(client, username="alice"):
    client.post("/api/auth/register", json={
        "username": username, "password": "senha1234", "email": f"{username}@x.com",
    })
    tok = client.post("/api/auth/login", json={"username": username, "password": "senha1234"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


class TestInventory:
    def test_crud_roundtrip(self, client):
        h = _auth(client)
        # cria
        r = client.post("/api/inventory", headers=h, json={
            "category": "Polvora", "name": "CBC 216", "quantity": 500, "unit": "g", "price_unit": 0.2,
        })
        assert r.status_code == 201
        item_id = r.json()["id"]
        # lista
        assert len(client.get("/api/inventory", headers=h).json()) == 1
        # atualiza
        r = client.put(f"/api/inventory/{item_id}", headers=h, json={
            "category": "Polvora", "name": "CBC 216", "quantity": 300, "unit": "g", "price_unit": 0.25,
        })
        assert r.json()["quantity"] == 300
        # apaga
        assert client.delete(f"/api/inventory/{item_id}", headers=h).status_code == 204
        assert client.get("/api/inventory", headers=h).json() == []

    def test_requires_auth(self, client):
        assert client.get("/api/inventory").status_code == 401
        assert client.post("/api/inventory", json={}).status_code == 401

    def test_negative_quantity_rejected(self, client):
        h = _auth(client)
        r = client.post("/api/inventory", headers=h, json={
            "category": "Polvora", "name": "X", "quantity": -1, "unit": "g",
        })
        assert r.status_code == 422

    def test_user_cannot_touch_anothers_item(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        item_id = client.post("/api/inventory", headers=ha, json={
            "category": "Polvora", "name": "CBC 216", "quantity": 10, "unit": "g",
        }).json()["id"]
        # bob nao ve o item de alice
        assert client.get("/api/inventory", headers=hb).json() == []
        # nem consegue editar ou apagar (404, nao vaza existencia)
        assert client.put(f"/api/inventory/{item_id}", headers=hb, json={
            "category": "Polvora", "name": "hack", "quantity": 0, "unit": "g",
        }).status_code == 404
        assert client.delete(f"/api/inventory/{item_id}", headers=hb).status_code == 404


class TestFirearms:
    def test_create_and_encrypted_fields_roundtrip(self, client):
        h = _auth(client)
        r = client.post("/api/firearms", headers=h, json={
            "model": "Glock G17", "serial": "ABC123", "sigma": "SG-999",
        })
        assert r.status_code == 201
        assert r.json()["serial"] == "ABC123"  # cifrado no banco, claro na resposta
        assert len(client.get("/api/firearms", headers=h).json()) == 1

    def test_isolation(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        gid = client.post("/api/firearms", headers=ha, json={"model": "Glock G17"}).json()["id"]
        assert client.get("/api/firearms", headers=hb).json() == []
        assert client.delete(f"/api/firearms/{gid}", headers=hb).status_code == 404


class TestLogbook:
    def test_create_defaults_date_today(self, client):
        h = _auth(client)
        r = client.post("/api/logbook", headers=h, json={"caliber": ".308 WIN", "quantity": 50})
        assert r.status_code == 201
        assert r.json()["date"]  # preenchido com hoje

    def test_firearm_must_belong_to_user(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        gid = client.post("/api/firearms", headers=ha, json={"model": "Glock"}).json()["id"]
        #  bob referenciando a arma de alice -> 404
        r = client.post("/api/logbook", headers=hb, json={
            "caliber": "9mm", "quantity": 10, "firearm_id": gid,
        })
        assert r.status_code == 404

    def test_isolation_and_delete(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        sid = client.post("/api/logbook", headers=ha, json={"caliber": "9mm", "quantity": 10}).json()["id"]
        assert client.get("/api/logbook", headers=hb).json() == []
        assert client.delete(f"/api/logbook/{sid}", headers=hb).status_code == 404
        assert client.delete(f"/api/logbook/{sid}", headers=ha).status_code == 204

    def test_update_changes_fields_and_keeps_date(self, client):
        h = _auth(client)
        created = client.post("/api/logbook", headers=h, json={
            "caliber": "9mm", "quantity": 10, "charge": 5.0,
        }).json()
        original_date = created["date"]
        r = client.put(f"/api/logbook/{created['id']}", headers=h, json={
            "caliber": "9mm Luger", "quantity": 25, "charge": 5.4, "velocity_avg": 1150,
        })
        assert r.status_code == 200
        body = r.json()
        assert body["caliber"] == "9mm Luger"
        assert body["quantity"] == 25
        assert body["velocity_avg"] == 1150
        assert body["date"] == original_date  # data preservada quando omitida

    def test_update_is_isolated(self, client):
        ha = _auth(client, "alice")
        hb = _auth(client, "bob")
        sid = client.post("/api/logbook", headers=ha, json={"caliber": "9mm", "quantity": 10}).json()["id"]
        r = client.put(f"/api/logbook/{sid}", headers=hb, json={"caliber": "hack", "quantity": 1})
        assert r.status_code == 404

    def test_create_without_deduct_leaves_inventory_untouched(self, client):
        h = _auth(client)
        client.post("/api/inventory", headers=h, json={
            "category": "Pólvora", "name": "CBC 216", "quantity": 100, "unit": "g", "price_unit": 0.5,
        })
        r = client.post("/api/logbook", headers=h, json={
            "caliber": ".38 SPL", "quantity": 50, "powder": "CBC 216", "charge": 3.0,
        })
        assert r.status_code == 201
        assert r.json()["deductions"] == []
        #  Sem deduct, o estoque nao muda.
        qty = client.get("/api/inventory", headers=h).json()[0]["quantity"]
        assert qty == 100

    def test_create_with_deduct_subtracts_and_prices(self, client):
        h = _auth(client)
        client.post("/api/inventory", headers=h, json={
            "category": "Pólvora", "name": "CBC 216", "quantity": 100, "unit": "g", "price_unit": 0.5,
        })
        client.post("/api/inventory", headers=h, json={
            "category": "Espoleta", "name": "Small Pistol", "quantity": 500, "unit": "un", "price_unit": 0.2,
        })
        r = client.post("/api/logbook?deduct=true", headers=h, json={
            "caliber": ".38 SPL", "quantity": 50, "powder": "CBC 216",
            "charge": 3.0, "primer": "Small Pistol",
        })
        assert r.status_code == 201
        body = r.json()
        assert len(body["deductions"]) == 2
        assert body["unit_cost"] and body["unit_cost"] > 0
        inv = {i["name"]: i["quantity"] for i in client.get("/api/inventory", headers=h).json()}
        #  3.0 gr x 50 = 150 grains = 150/15.4324 ~= 9.72 g deduzidos.
        assert inv["CBC 216"] == pytest.approx(100 - 150 / 15.4324, abs=0.01)
        assert inv["Small Pistol"] == 450

    def test_deduct_reports_insufficient_stock(self, client):
        h = _auth(client)
        client.post("/api/inventory", headers=h, json={
            "category": "Espoleta", "name": "Small Pistol", "quantity": 10, "unit": "un", "price_unit": 0.2,
        })
        r = client.post("/api/logbook?deduct=true", headers=h, json={
            "caliber": ".38 SPL", "quantity": 50, "primer": "Small Pistol",
        })
        assert r.status_code == 201
        assert any("insuficiente" in d.lower() for d in r.json()["deductions"])
        #  Estoque insuficiente nao e debitado.
        assert client.get("/api/inventory", headers=h).json()[0]["quantity"] == 10
