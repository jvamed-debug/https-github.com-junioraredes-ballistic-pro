"""Testes do mailer (Resend via API HTTP e detecção de configuração)."""

import services.mailer as mailer


def test_nothing_configured_returns_false(monkeypatch):
    for k in ("RESEND_API_KEY", "RESEND_FROM", "SMTP_HOST", "SMTP_FROM", "SMTP_USER"):
        monkeypatch.delenv(k, raising=False)
    assert mailer.email_configured() is False
    assert mailer.send_email("a@b.com", "s", "b") is False


def test_resend_configured_detects_key_and_from(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("RESEND_FROM", "no-reply@x.com")
    assert mailer.resend_configured() is True
    assert mailer.email_configured() is True


def test_resend_send_posts_to_api(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("RESEND_FROM", "no-reply@x.com")
    monkeypatch.delenv("SMTP_HOST", raising=False)

    calls = {}

    class _Resp:
        status_code = 200

    def _fake_post(url, headers=None, json=None, timeout=None):
        calls["url"] = url
        calls["headers"] = headers
        calls["json"] = json
        return _Resp()

    import requests
    monkeypatch.setattr(requests, "post", _fake_post)

    ok = mailer.send_password_reset("user@x.com", "https://app/?reset=tok")
    assert ok is True
    assert calls["url"] == "https://api.resend.com/emails"
    assert calls["headers"]["Authorization"] == "Bearer re_test"
    assert calls["json"]["to"] == ["user@x.com"]
    assert calls["json"]["from"] == "no-reply@x.com"
    assert "reset=tok" in calls["json"]["text"]


def test_resend_failure_returns_false(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("RESEND_FROM", "no-reply@x.com")
    monkeypatch.delenv("SMTP_HOST", raising=False)

    class _Resp:
        status_code = 422

    import requests
    monkeypatch.setattr(requests, "post", lambda *a, **k: _Resp())
    assert mailer.send_email("user@x.com", "s", "b") is False
