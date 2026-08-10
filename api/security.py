"""Autenticacao por token (JWT) para a API.

Reaproveita o login existente (core.auth.authenticate, sobre bcrypt): a API
so emite e valida um token assinado; a verificacao de senha e o hashing
continuam onde sempre estiveram. O segredo do JWT vem de JWT_SECRET; na falta
dele cai para FERNET_KEY (ja presente em producao) e, por ultimo, um valor de
desenvolvimento — que dispara aviso e nunca deve ir a producao.
"""

from __future__ import annotations

import os
import warnings
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from core.models import User, managed_session

ALGORITHM = "HS256"
TOKEN_TTL = timedelta(hours=12)

#  auto_error=False para podermos lancar 401 com mensagem propria e cabecalho
#  WWW-Authenticate coerente.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

_DEV_SECRET = "dev-insecure-jwt-secret-change-me"


def _secret() -> str:
    secret = os.getenv("JWT_SECRET") or os.getenv("FERNET_KEY")
    if not secret:
        warnings.warn(
            "[SECURITY] JWT_SECRET/FERNET_KEY ausentes — usando segredo de "
            "desenvolvimento. NAO use assim em producao.",
            stacklevel=2,
        )
        return _DEV_SECRET
    return secret


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "iat": now, "exp": now + TOKEN_TTL}
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def serialize_user(user: User) -> dict:
    """Materializa o usuario num dict DENTRO da sessao — as colunas PII sao
    descriptografadas na leitura e ficariam indisponiveis apos o detach."""
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "cpf": user.cpf,
        "cr_number": user.cr_number,
        "cr_expiration": user.cr_expiration,
        "address_acervo": user.address_acervo,
        "is_premium": bool(user.is_premium),
    }


def get_current_user(token: str | None = Depends(oauth2_scheme)) -> dict:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nao autenticado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise cred_exc
    try:
        payload = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        raise cred_exc

    with managed_session() as db:
        user = db.get(User, user_id)
        if not user:
            raise cred_exc
        return serialize_user(user)
