"""Envio de e-mail transacional (recuperacao de senha), opcional por SMTP.

Se as variaveis SMTP_* nao estiverem definidas, `send_email` apenas retorna
False (nao envia) — o chamador decide o que fazer (ex.: logar o link). Assim a
API funciona sem servidor de e-mail, e passa a enviar de verdade quando o
ambiente for configurado. Nunca levanta excecao para o fluxo de auth.
"""

from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage


def smtp_configured() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM"))


def app_base_url() -> str:
    """URL base do app para montar links (sem barra final)."""
    return os.getenv("APP_BASE_URL", "http://localhost:5173").rstrip("/")


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Envia um e-mail de texto. Retorna True se enviou, False se SMTP nao
    esta configurado ou se o envio falhou (sem levantar)."""
    if not smtp_configured() or not to_email:
        return False
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


def send_password_reset(to_email: str, reset_url: str) -> bool:
    body = (
        "Você (ou alguém) pediu a redefinição da sua senha no Ballistic Pro.\n\n"
        f"Para criar uma nova senha, abra o link abaixo:\n{reset_url}\n\n"
        "O link expira em 1 hora e só pode ser usado uma vez. Se não foi você, "
        "ignore este e-mail — sua senha atual continua valendo."
    )
    return send_email(to_email, "Redefinição de senha — Ballistic Pro", body)
