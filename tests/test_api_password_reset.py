"""Testes do fluxo de recuperação de senha (esqueci minha senha)."""

import importlib
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    #  Sem SMTP, expõe o token na resposta para testar o fluxo ponta a ponta.
    monkeypatch.setenv("AUTH_RESET_EXPOSE_TOKEN", "1")

    import core.models as models
    importlib.reload(models)
    import core.auth as auth
    importlib.reload(auth)
    import api.security as security
    importlib.reload(security)
    for mod in ("api.routers.auth", "api.main"):
        importlib.reload(importlib.import_module(mod))
    import api.main as main

    models.Base.metadata.create_all(models.engine)
    models.ensure_schema_compliance(models.engine)
    return TestClient(main.app), models


def _register(client, username="joao", email="joao@x.com", password="senha1234"):
    client.post("/api/auth/register", json={
        "username": username, "password": password, "email": email,
    })


class TestForgotPassword:
    def test_generic_response_and_token_for_known_email(self, client):
        c, _ = client
        _register(c)
        r = c.post("/api/auth/forgot-password", json={"identifier": "joao@x.com"})
        assert r.status_code == 200
        assert "redefini" in r.json()["detail"].lower()
        assert r.json()["reset_token"]  # exposto porque AUTH_RESET_EXPOSE_TOKEN=1

    def test_unknown_identifier_no_token_same_message(self, client):
        c, _ = client
        _register(c)
        r = c.post("/api/auth/forgot-password", json={"identifier": "ninguem@x.com"})
        assert r.status_code == 200
        assert r.json()["reset_token"] is None  # não vaza que a conta não existe

    def test_works_by_username_too(self, client):
        c, _ = client
        _register(c)
        r = c.post("/api/auth/forgot-password", json={"identifier": "joao"})
        assert r.json()["reset_token"]


class TestResetPassword:
    def _token(self, c, ident="joao@x.com"):
        return c.post("/api/auth/forgot-password", json={"identifier": ident}).json()["reset_token"]

    def test_reset_changes_password(self, client):
        c, _ = client
        _register(c)
        tok = self._token(c)
        r = c.post("/api/auth/reset-password", json={"token": tok, "new_password": "novaSenha9"})
        assert r.status_code == 200
        assert c.post("/api/auth/login", json={"username": "joao", "password": "novaSenha9"}).status_code == 200
        assert c.post("/api/auth/login", json={"username": "joao", "password": "senha1234"}).status_code == 401

    def test_token_is_single_use(self, client):
        c, _ = client
        _register(c)
        tok = self._token(c)
        assert c.post("/api/auth/reset-password", json={"token": tok, "new_password": "novaSenha9"}).status_code == 200
        assert c.post("/api/auth/reset-password", json={"token": tok, "new_password": "outraSenha9"}).status_code == 400

    def test_invalid_token_rejected(self, client):
        c, _ = client
        _register(c)
        assert c.post("/api/auth/reset-password", json={"token": "x" * 40, "new_password": "abcd1234"}).status_code == 400

    def test_short_password_rejected(self, client):
        c, _ = client
        _register(c)
        tok = self._token(c)
        assert c.post("/api/auth/reset-password", json={"token": tok, "new_password": "123"}).status_code == 422

    def test_expired_token_rejected(self, client):
        c, models = client
        _register(c)
        tok = self._token(c)
        #  Força o vencimento no banco.
        with models.managed_session() as s:
            pr = s.query(models.PasswordReset).first()
            pr.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        r = c.post("/api/auth/reset-password", json={"token": tok, "new_password": "novaSenha9"})
        assert r.status_code == 400
        assert "expir" in r.json()["detail"].lower()

    def test_new_token_invalidates_previous(self, client):
        c, _ = client
        _register(c)
        first = self._token(c)
        second = self._token(c)
        #  Ao usar o segundo, o primeiro (ainda pendente) também é invalidado.
        assert c.post("/api/auth/reset-password", json={"token": second, "new_password": "novaSenha9"}).status_code == 200
        assert c.post("/api/auth/reset-password", json={"token": first, "new_password": "outraSenha9"}).status_code == 400
