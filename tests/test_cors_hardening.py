"""Teste do aviso de CORS aberto em produção (auditoria F5)."""

import importlib


def _reload_main(monkeypatch, **env):
    for k in ("API_CORS_ORIGINS", "FERNET_KEY", "DATABASE_URL", "JWT_SECRET"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import api.main as main
    importlib.reload(main)
    return main


def test_warns_when_star_in_production(monkeypatch, capsys):
    _reload_main(monkeypatch, DATABASE_URL="postgresql://u:p@h/db")  # produção + '*' default
    out = capsys.readouterr().out
    assert "API_CORS_ORIGINS='*' em producao" in out


def test_no_warning_with_explicit_origins(monkeypatch, capsys):
    m = _reload_main(monkeypatch, DATABASE_URL="postgresql://u:p@h/db",
                     API_CORS_ORIGINS="https://app.exemplo.com")
    out = capsys.readouterr().out
    assert "em producao" not in out
    assert m.allow_origins == ["https://app.exemplo.com"]


def test_no_warning_in_dev(monkeypatch, capsys):
    _reload_main(monkeypatch)  # sem FERNET_KEY nem Postgres → dev
    out = capsys.readouterr().out
    assert "em producao" not in out
