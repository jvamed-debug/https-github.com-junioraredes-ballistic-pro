"""Testes do endurecimento do segredo de assinatura do JWT (auditoria P1)."""

import importlib

import pytest


def _reload_security(monkeypatch, **env):
    #  Limpa as três variáveis relevantes e aplica o cenário do teste.
    for k in ("JWT_SECRET", "FERNET_KEY", "DATABASE_URL"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import api.security as security
    importlib.reload(security)
    return security


class TestJwtSecretResolution:
    def test_prefers_jwt_secret(self, monkeypatch):
        s = _reload_security(monkeypatch, JWT_SECRET="proper-secret", FERNET_KEY="fk")
        assert s._secret() == "proper-secret"

    def test_falls_back_to_fernet_with_warning(self, monkeypatch):
        s = _reload_security(monkeypatch, FERNET_KEY="fk-only")
        with pytest.warns(UserWarning, match="reuso de chave"):
            assert s._secret() == "fk-only"

    def test_production_without_any_secret_raises(self, monkeypatch):
        #  Produção detectada pelo Postgres, sem FERNET_KEY nem JWT_SECRET.
        s = _reload_security(monkeypatch, DATABASE_URL="postgresql://u@h/db")
        with pytest.raises(RuntimeError, match="JWT_SECRET ausente em producao"):
            s._secret()

    def test_dev_without_secret_uses_dev_value_with_warning(self, monkeypatch):
        s = _reload_security(monkeypatch)  # nada definido → desenvolvimento
        with pytest.warns(UserWarning, match="segredo de desenvolvimento"):
            assert s._secret() == s._DEV_SECRET

    def test_dev_secret_never_returned_in_production(self, monkeypatch):
        #  Em produção, o valor de dev nunca é retornado: ou usa FERNET_KEY,
        #  ou levanta — mas nunca cai no _DEV_SECRET.
        s = _reload_security(monkeypatch, DATABASE_URL="postgresql://u@h/db")
        try:
            got = s._secret()
        except RuntimeError:
            got = None
        assert got != s._DEV_SECRET

    def test_token_roundtrip_with_jwt_secret(self, monkeypatch):
        s = _reload_security(monkeypatch, JWT_SECRET="rt-secret")
        import jwt
        tok = s.create_access_token(42)
        payload = jwt.decode(tok, "rt-secret", algorithms=[s.ALGORITHM])
        assert payload["sub"] == "42"
