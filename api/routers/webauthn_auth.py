"""Login por biometria via WebAuthn (passkeys).

O navegador guarda uma chave privada no autenticador do aparelho (Face ID,
Touch ID, sensor de digital, chave de seguranca) e so a libera apos a
verificacao biometrica do dono. O servidor guarda apenas a chave PUBLICA e,
a cada cerimonia, um desafio aleatorio que a assinatura precisa cobrir.

A dependencia `webauthn` (py_webauthn) e OPCIONAL: sem ela, ou sem o dominio
configurado (WEBAUTHN_RP_ID/WEBAUTHN_RP_ORIGIN), o recurso fica desligado e os
endpoints respondem 503 — o login por senha continua funcionando normalmente.

Config por ambiente:
    WEBAUTHN_RP_ID      dominio do app (ex.: app.seudominio.com) — sem https://
    WEBAUTHN_RP_ORIGIN  origem completa (ex.: https://app.seudominio.com)
    WEBAUTHN_RP_NAME    nome exibido (default "Ballistic Pro")
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas import (
    TokenResponse,
    WebAuthnAvailable,
    WebAuthnLoginBegin,
    WebAuthnLoginComplete,
    WebAuthnRegisterComplete,
)
from api.security import create_access_token, get_current_user
from core.models import User, WebAuthnCredential, WebAuthnChallenge, managed_session

try:  # A lib e opcional; o app tem de importar mesmo sem ela.
    from webauthn import (
        generate_authentication_options,
        generate_registration_options,
        options_to_json,
        verify_authentication_response,
        verify_registration_response,
    )
    from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
    from webauthn.helpers.structs import (
        AuthenticatorSelectionCriteria,
        PublicKeyCredentialDescriptor,
        ResidentKeyRequirement,
        UserVerificationRequirement,
    )

    HAS_WEBAUTHN = True
except Exception:  # pragma: no cover - caminho sem a lib instalada
    HAS_WEBAUTHN = False

router = APIRouter(prefix="/api/auth/webauthn", tags=["webauthn"])

#  Desafio expira: uma cerimonia que nao terminou em minutos foi abandonada.
CHALLENGE_TTL = timedelta(minutes=10)


def _config() -> tuple[str, str, str] | None:
    rp_id = os.getenv("WEBAUTHN_RP_ID")
    if not rp_id:
        return None
    rp_name = os.getenv("WEBAUTHN_RP_NAME", "Ballistic Pro")
    #  Sem origem explicita, assume https no mesmo dominio (o caso comum).
    rp_origin = os.getenv("WEBAUTHN_RP_ORIGIN", f"https://{rp_id}")
    return rp_id, rp_name, rp_origin


def _enabled() -> bool:
    return HAS_WEBAUTHN and _config() is not None


def _require_enabled() -> tuple[str, str, str]:
    cfg = _config()
    if not HAS_WEBAUTHN or cfg is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login por biometria nao esta disponivel neste servidor.",
        )
    return cfg


def _store_challenge(db, key: str, purpose: str, challenge: bytes) -> None:
    #  Uma cerimonia por chave: limpa desafios anteriores antes de guardar.
    db.query(WebAuthnChallenge).filter_by(key=key, purpose=purpose).delete()
    db.add(WebAuthnChallenge(
        key=key, purpose=purpose, challenge=bytes_to_base64url(challenge),
    ))


def _take_challenge(db, key: str, purpose: str) -> bytes:
    row = (
        db.query(WebAuthnChallenge)
        .filter_by(key=key, purpose=purpose)
        .order_by(WebAuthnChallenge.id.desc())
        .first()
    )
    if row is None:
        raise HTTPException(status_code=400, detail="Desafio nao encontrado ou expirado.")
    created = row.created_at
    if created is not None and created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    expired = created is not None and datetime.now(timezone.utc) - created > CHALLENGE_TTL
    challenge = base64url_to_bytes(row.challenge)
    db.delete(row)  # consumido — de uso unico, valido ou nao
    if expired:
        raise HTTPException(status_code=400, detail="Desafio expirado. Tente de novo.")
    return challenge


@router.get("/available", response_model=WebAuthnAvailable)
def available() -> WebAuthnAvailable:
    """Diz ao app se deve oferecer o login por biometria."""
    return WebAuthnAvailable(available=_enabled())


@router.post("/register/begin")
def register_begin(current=Depends(get_current_user)) -> dict:
    """Opcoes para cadastrar uma passkey (usuario ja autenticado por senha)."""
    rp_id, rp_name, _ = _require_enabled()
    with managed_session() as db:
        existing = db.query(WebAuthnCredential).filter_by(user_id=current["id"]).all()
        exclude = [
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(c.credential_id))
            for c in existing
        ]
        options = generate_registration_options(
            rp_id=rp_id,
            rp_name=rp_name,
            user_name=current["username"],
            user_id=str(current["id"]).encode(),
            user_display_name=current.get("name") or current["username"],
            exclude_credentials=exclude,
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.PREFERRED,
                user_verification=UserVerificationRequirement.PREFERRED,
            ),
        )
        _store_challenge(db, f"reg:{current['id']}", "register", options.challenge)
    return json.loads(options_to_json(options))


@router.post("/register/complete")
def register_complete(body: WebAuthnRegisterComplete, current=Depends(get_current_user)) -> dict:
    """Verifica a resposta do autenticador e guarda a chave publica."""
    rp_id, _, rp_origin = _require_enabled()
    with managed_session() as db:
        challenge = _take_challenge(db, f"reg:{current['id']}", "register")
        try:
            verified = verify_registration_response(
                credential=body.credential,
                expected_challenge=challenge,
                expected_rp_id=rp_id,
                expected_origin=rp_origin,
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Falha ao registrar passkey: {exc}")

        cred_id = bytes_to_base64url(verified.credential_id)
        if db.query(WebAuthnCredential).filter_by(credential_id=cred_id).first():
            raise HTTPException(status_code=409, detail="Esta passkey ja esta cadastrada.")
        db.add(WebAuthnCredential(
            user_id=current["id"],
            credential_id=cred_id,
            public_key=bytes_to_base64url(verified.credential_public_key),
            sign_count=verified.sign_count,
            label=body.label,
        ))
    return {"detail": "Passkey cadastrada."}


@router.post("/login/begin")
def login_begin(body: WebAuthnLoginBegin) -> dict:
    """Opcoes para autenticar com uma passkey ja cadastrada."""
    rp_id, _, _ = _require_enabled()
    with managed_session() as db:
        user = db.query(User).filter_by(username=body.username).first()
        creds = (
            db.query(WebAuthnCredential).filter_by(user_id=user.id).all() if user else []
        )
        if not creds:
            raise HTTPException(status_code=404, detail="Nenhuma passkey cadastrada para este usuario.")
        options = generate_authentication_options(
            rp_id=rp_id,
            allow_credentials=[
                PublicKeyCredentialDescriptor(id=base64url_to_bytes(c.credential_id))
                for c in creds
            ],
            user_verification=UserVerificationRequirement.PREFERRED,
        )
        _store_challenge(db, f"login:{body.username}", "login", options.challenge)
    return json.loads(options_to_json(options))


@router.post("/login/complete", response_model=TokenResponse)
def login_complete(body: WebAuthnLoginComplete) -> TokenResponse:
    """Verifica a assinatura e devolve o token JWT (mesmo do login por senha)."""
    rp_id, _, rp_origin = _require_enabled()
    raw_id = body.credential.get("rawId") or body.credential.get("id")
    if not raw_id:
        raise HTTPException(status_code=400, detail="Credencial invalida.")

    with managed_session() as db:
        challenge = _take_challenge(db, f"login:{body.username}", "login")
        user = db.query(User).filter_by(username=body.username).first()
        cred = (
            db.query(WebAuthnCredential)
            .filter_by(credential_id=raw_id, user_id=user.id)
            .first()
            if user
            else None
        )
        if cred is None:
            raise HTTPException(status_code=401, detail="Passkey nao reconhecida.")
        try:
            verified = verify_authentication_response(
                credential=body.credential,
                expected_challenge=challenge,
                expected_rp_id=rp_id,
                expected_origin=rp_origin,
                credential_public_key=base64url_to_bytes(cred.public_key),
                credential_current_sign_count=cred.sign_count,
            )
        except Exception as exc:
            raise HTTPException(status_code=401, detail=f"Falha na autenticacao: {exc}")

        cred.sign_count = verified.new_sign_count
        token = create_access_token(user.id)
    return TokenResponse(access_token=token)
