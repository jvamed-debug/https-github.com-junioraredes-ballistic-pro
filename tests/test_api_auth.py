"""Testes dos endpoints de auth/perfil da API, rodando em MODO PRODUCAO
(FERNET_KEY ligada). Espelham o fixture de test_security: sem a cifra ativa,
os bugs de unicidade/busca por blind index ficam invisiveis — entao a API
precisa ser exercitada com a criptografia PII ligada.
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
    monkeypatch.setenv("JWT_SECRET", "test-secret-para-os-testes")

    #  Recarrega dominio e API para que engine e tokens apontem ao ambiente do
    #  teste. A ordem importa: os modulos da api referenciam os do core.
    import core.models as models
    importlib.reload(models)
    import core.auth as auth
    importlib.reload(auth)
    import api.security as security
    importlib.reload(security)
    import api.routers.auth as auth_router
    importlib.reload(auth_router)
    import api.routers.ballistics as ballistics_router
    importlib.reload(ballistics_router)
    import api.main as main
    importlib.reload(main)

    models.Base.metadata.create_all(models.engine)
    models.ensure_schema_compliance(models.engine)

    yield TestClient(main.app)


def _register(client, **over):
    body = {
        "username": "alice",
        "password": "senha1234",
        "name": "Alice",
        "cpf": "12345678900",
        "email": "alice@example.com",
        "phone": None,
    }
    body.update(over)
    return client.post("/api/auth/register", json=body)


def _token(client, **over):
    _register(client, **over)
    username = over.get("username", "alice")
    password = over.get("password", "senha1234")
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


class TestRegisterLogin:
    def test_register_then_login_returns_token(self, client):
        assert _register(client).status_code == 201
        r = client.post("/api/auth/login", json={"username": "alice", "password": "senha1234"})
        assert r.status_code == 200
        assert r.json()["token_type"] == "bearer"
        assert r.json()["access_token"]

    def test_short_password_is_rejected(self, client):
        assert _register(client, password="123").status_code == 422

    def test_duplicate_email_is_rejected(self, client):
        assert _register(client).status_code == 201
        r = _register(client, username="bob", cpf="98765432100", email="alice@example.com")
        assert r.status_code == 400

    def test_wrong_password_is_401(self, client):
        _register(client)
        r = client.post("/api/auth/login", json={"username": "alice", "password": "errada99"})
        assert r.status_code == 401


class TestLockout:
    def test_lockout_after_threshold_returns_429(self, client):
        _register(client)
        import core.auth as auth
        for _ in range(auth.LOCKOUT_THRESHOLD):
            client.post("/api/auth/login", json={"username": "alice", "password": "errada99"})
        r = client.post("/api/auth/login", json={"username": "alice", "password": "senha1234"})
        assert r.status_code == 429

    def test_success_clears_the_counter(self, client):
        _register(client)
        import core.auth as auth
        for _ in range(auth.LOCKOUT_THRESHOLD - 1):
            client.post("/api/auth/login", json={"username": "alice", "password": "errada99"})
        #  Ainda abaixo do limite: login certo passa e zera o contador.
        assert client.post("/api/auth/login", json={"username": "alice", "password": "senha1234"}).status_code == 200


class TestMe:
    def test_me_requires_token(self, client):
        assert client.get("/api/auth/me").status_code == 401

    def test_me_rejects_garbage_token(self, client):
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer nao-e-um-jwt"})
        assert r.status_code == 401

    def test_me_returns_the_user(self, client):
        token = _token(client)
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"
        assert data["cpf"] == "12345678900"


class TestProfileUpdate:
    def test_update_changes_fields_and_keeps_search_working(self, client):
        token = _token(client)
        headers = {"Authorization": f"Bearer {token}"}
        r = client.put("/api/auth/me", headers=headers, json={"email": "nova@example.com", "name": "Alice B"})
        assert r.status_code == 200
        assert r.json()["email"] == "nova@example.com"
        assert r.json()["name"] == "Alice B"

        #  A recuperacao (busca por blind index) tem de achar pelo NOVO email,
        #  provando que o hash foi recalculado no update.
        import core.models as models
        client.post("/api/auth/recover", json={"identifier": "nova@example.com"})
        with models.managed_session() as db:
            found = db.query(models.AuditLog).filter_by(action="auth_recovery_requested").count()
        assert found == 1

    def test_update_normalizes_cpf(self, client):
        token = _token(client)
        headers = {"Authorization": f"Bearer {token}"}
        r = client.put("/api/auth/me", headers=headers, json={"cpf": "111.222.333-44"})
        assert r.status_code == 200
        assert r.json()["cpf"] == "11122233344"

    def test_update_requires_token(self, client):
        assert client.put("/api/auth/me", json={"name": "X"}).status_code == 401


class TestRecover:
    def test_recover_is_generic_regardless_of_existence(self, client):
        miss = client.post("/api/auth/recover", json={"identifier": "naoexiste@example.com"})
        assert miss.status_code == 200
        _register(client)
        hit = client.post("/api/auth/recover", json={"identifier": "alice@example.com"})
        assert hit.json()["detail"] == miss.json()["detail"]
