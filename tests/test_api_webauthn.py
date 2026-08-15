"""Testes do login por biometria (WebAuthn / passkeys).

Cobrem o que da para cobrir sem um autenticador de verdade:

- Modo DESLIGADO (sem WEBAUTHN_RP_ID ou sem a lib): available=false e 503 nos
  endpoints — roda em qualquer ambiente.
- Modo LIGADO (lib presente + dominio configurado): geracao de opcoes de
  registro/login, exigencia de autenticacao, 404 sem passkey e rejeicao de
  credencial desconhecida. A verificacao criptografica do caminho feliz
  depende de um autenticador real e fica para teste manual/dispositivo.
"""

import importlib

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient


def _build(tmp_path, monkeypatch, rp_id=None):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    if rp_id:
        monkeypatch.setenv("WEBAUTHN_RP_ID", rp_id)
        monkeypatch.setenv("WEBAUTHN_RP_ORIGIN", f"https://{rp_id}")
    else:
        monkeypatch.delenv("WEBAUTHN_RP_ID", raising=False)

    import core.models as models
    importlib.reload(models)
    import core.auth as auth
    importlib.reload(auth)
    import api.security as security
    importlib.reload(security)
    for mod in ("api.routers.auth", "api.routers.data", "api.routers.webauthn_auth", "api.main"):
        importlib.reload(importlib.import_module(mod))
    import api.main as main

    models.Base.metadata.create_all(models.engine)
    models.ensure_schema_compliance(models.engine)
    return main, models


def _auth(client, username="alice"):
    client.post("/api/auth/register", json={"username": username, "password": "senha1234"})
    tok = client.post("/api/auth/login", json={
        "username": username, "password": "senha1234",
    }).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _seed_credential(models, username="alice", cred_id="AAAA"):
    with models.managed_session() as db:
        user = db.query(models.User).filter_by(username=username).first()
        db.add(models.WebAuthnCredential(
            user_id=user.id, credential_id=cred_id, public_key="BBBB", sign_count=0,
        ))


class TestDisabled:
    def test_available_false(self, tmp_path, monkeypatch):
        main, _ = _build(tmp_path, monkeypatch, rp_id=None)
        c = TestClient(main.app)
        assert c.get("/api/auth/webauthn/available").json() == {"available": False}

    def test_endpoints_return_503(self, tmp_path, monkeypatch):
        main, _ = _build(tmp_path, monkeypatch, rp_id=None)
        c = TestClient(main.app)
        h = _auth(c)
        assert c.post("/api/auth/webauthn/register/begin", headers=h).status_code == 503
        assert c.post("/api/auth/webauthn/login/begin", json={"username": "alice"}).status_code == 503


class TestEnabled:
    def test_available_true(self, tmp_path, monkeypatch):
        pytest.importorskip("webauthn")
        main, _ = _build(tmp_path, monkeypatch, rp_id="localhost")
        c = TestClient(main.app)
        assert c.get("/api/auth/webauthn/available").json() == {"available": True}

    def test_register_begin_requires_auth(self, tmp_path, monkeypatch):
        pytest.importorskip("webauthn")
        main, _ = _build(tmp_path, monkeypatch, rp_id="localhost")
        c = TestClient(main.app)
        assert c.post("/api/auth/webauthn/register/begin").status_code == 401

    def test_register_begin_returns_options(self, tmp_path, monkeypatch):
        pytest.importorskip("webauthn")
        main, _ = _build(tmp_path, monkeypatch, rp_id="localhost")
        c = TestClient(main.app)
        h = _auth(c)
        r = c.post("/api/auth/webauthn/register/begin", headers=h)
        assert r.status_code == 200
        opts = r.json()
        assert opts["rp"]["id"] == "localhost"
        assert opts["user"]["name"] == "alice"
        assert opts.get("challenge")

    def test_login_begin_404_without_passkey(self, tmp_path, monkeypatch):
        pytest.importorskip("webauthn")
        main, _ = _build(tmp_path, monkeypatch, rp_id="localhost")
        c = TestClient(main.app)
        _auth(c)  # cria alice, sem passkey
        assert c.post("/api/auth/webauthn/login/begin", json={"username": "alice"}).status_code == 404

    def test_login_begin_returns_allow_credentials(self, tmp_path, monkeypatch):
        pytest.importorskip("webauthn")
        main, models = _build(tmp_path, monkeypatch, rp_id="localhost")
        c = TestClient(main.app)
        _auth(c)
        _seed_credential(models)
        r = c.post("/api/auth/webauthn/login/begin", json={"username": "alice"})
        assert r.status_code == 200
        assert any(d["id"] == "AAAA" for d in r.json().get("allowCredentials", []))

    def test_login_complete_rejects_unknown_credential(self, tmp_path, monkeypatch):
        pytest.importorskip("webauthn")
        main, models = _build(tmp_path, monkeypatch, rp_id="localhost")
        c = TestClient(main.app)
        _auth(c)
        _seed_credential(models)
        c.post("/api/auth/webauthn/login/begin", json={"username": "alice"})  # cria desafio
        r = c.post("/api/auth/webauthn/login/complete", json={
            "username": "alice",
            "credential": {"rawId": "ZZZZ", "id": "ZZZZ", "response": {}},
        })
        assert r.status_code == 401

    def test_login_complete_without_challenge_is_400(self, tmp_path, monkeypatch):
        pytest.importorskip("webauthn")
        main, models = _build(tmp_path, monkeypatch, rp_id="localhost")
        c = TestClient(main.app)
        _auth(c)
        _seed_credential(models)
        #  Sem passar por login/begin, nao ha desafio guardado.
        r = c.post("/api/auth/webauthn/login/complete", json={
            "username": "alice",
            "credential": {"rawId": "AAAA", "id": "AAAA", "response": {}},
        })
        assert r.status_code == 400
