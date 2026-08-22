"""Envio de e-mail transacional (recuperacao de senha), opcional.

Dois back-ends, nesta ordem de preferencia:
  1. Resend (API HTTP) — quando RESEND_API_KEY esta definido. Usa HTTPS (443),
     que costuma passar mesmo onde as portas de SMTP estao bloqueadas.
  2. SMTP — quando SMTP_HOST/SMTP_FROM estao definidos.

Sem nenhum dos dois, `send_email` retorna False (nao envia) e o chamador decide
o que fazer (ex.: logar o link). Nunca levanta excecao para o fluxo de auth.
"""

from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage


def _mail_from() -> str:
    #  Remetente comum aos dois back-ends. RESEND_FROM tem prioridade; senao
    #  cai para SMTP_FROM (ou o proprio usuario SMTP).
    return os.getenv("RESEND_FROM") or os.getenv("SMTP_FROM") or os.getenv("SMTP_USER") or ""


def resend_configured() -> bool:
    return bool(os.getenv("RESEND_API_KEY") and _mail_from())


def smtp_configured() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM"))


def email_configured() -> bool:
    return resend_configured() or smtp_configured()


def app_base_url() -> str:
    """URL base do app para montar links (sem barra final)."""
    return os.getenv("APP_BASE_URL", "http://localhost:5173").rstrip("/")


def _send_resend(to_email: str, subject: str, body: str) -> bool:
    try:
        import requests
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {os.getenv('RESEND_API_KEY')}",
                "Content-Type": "application/json",
            },
            json={"from": _mail_from(), "to": [to_email], "subject": subject, "text": body},
            timeout=15,
        )
        return resp.status_code in (200, 201)
    except Exception:
        return False


def _send_smtp(to_email: str, subject: str, body: str) -> bool:
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM", user or "")
    use_ssl = os.getenv("SMTP_SSL", "").lower() in ("1", "true", "yes")

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context()) as s:
                if user and password:
                    s.login(user, password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port) as s:
                s.starttls(context=ssl.create_default_context())
                if user and password:
                    s.login(user, password)
                s.send_message(msg)
        return True
    except Exception:
        return False


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Envia um e-mail de texto. True se enviou; False se nao ha back-end
    configurado ou se o envio falhou (sem levantar). Tenta Resend, depois SMTP."""
    if not to_email:
        return False
    if resend_configured() and _send_resend(to_email, subject, body):
        return True
    if smtp_configured():
        return _send_smtp(to_email, subject, body)
    return False


def send_password_reset(to_email: str, reset_url: str) -> bool:
    body = (
        "Você (ou alguém) pediu a redefinição da sua senha no Ballistic Pro.\n\n"
        f"Para criar uma nova senha, abra o link abaixo:\n{reset_url}\n\n"
        "O link expira em 1 hora e só pode ser usado uma vez. Se não foi você, "
        "ignore este e-mail — sua senha atual continua valendo."
    )
    return send_email(to_email, "Redefinição de senha — Ballistic Pro", body)
