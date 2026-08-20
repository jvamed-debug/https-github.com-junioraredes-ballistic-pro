"""Endpoints de autenticacao e perfil.

Toda a logica sensivel (verificacao de senha, unicidade por blind index,
bloqueio de forca-bruta, recuperacao anti-enumeracao) ja vive em core.auth e e
reaproveitada aqui — a API so acrescenta a emissao/validacao do token JWT.
"""

import os
import re

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    MessageResponse,
    ProfileUpdateRequest,
    RecoverRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserOut,
)
from api.security import create_access_token, get_current_user, serialize_user
from core.auth import (
    authenticate,
    clear_login_attempts,
    create_reset_token,
    login_lock_remaining,
    record_failed_login,
    recover_password,
    register_user,
    reset_password_with_token,
)
from core.models import User, managed_session
from schemas import ProfileUpdate
from services.mailer import app_base_url, send_password_reset

router = APIRouter(prefix="/api/auth", tags=["auth"])

#  Mensagem generica (anti-enumeracao): mesma resposta havendo conta ou nao.
_FORGOT_MSG = (
    "Se os dados informados corresponderem a uma conta, enviaremos um link de "
    "redefinição de senha. Verifique seu e-mail."
)


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest) -> MessageResponse:
    ok, message = register_user(
        req.username, req.password, req.name, req.cpf, req.email, req.phone
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return MessageResponse(detail=message)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest) -> TokenResponse:
    #  Bloqueio de forca-bruta persistido no servidor, keyed pelo login
    #  tentado — reconectar nao zera a contagem.
    remaining = login_lock_remaining(req.username)
    if remaining > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Muitas tentativas falhas. Tente novamente em {remaining}s.",
        )

    user = authenticate(req.username, req.password)
    if not user:
        record_failed_login(req.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas.",
        )

    clear_login_attempts(req.username)
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/recover", response_model=MessageResponse)
def recover(req: RecoverRequest) -> MessageResponse:
    #  Resposta sempre generica (anti-enumeracao) — a decisao de logar ou nao
    #  fica dentro de recover_password.
    _, message = recover_password(req.identifier)
    return MessageResponse(detail=message)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(req: ForgotPasswordRequest) -> ForgotPasswordResponse:
    """Gera o link de recuperação e o envia por e-mail (se SMTP configurado).

    Resposta sempre genérica — nunca revela se a conta existe. Se não houver
    SMTP e AUTH_RESET_EXPOSE_TOKEN estiver ligado, o token volta na resposta
    (apenas para uso em dev/teste).
    """
    token, email = create_reset_token(req.identifier)
    reset_token = None
    if token:
        reset_url = f"{app_base_url()}/?reset={token}"
        sent = send_password_reset(email or "", reset_url)
        #  Sem e-mail configurado/entregue: expoe o token so se explicitamente
        #  autorizado (dev/teste). Em producao com SMTP, nunca vaza.
        if not sent and os.getenv("AUTH_RESET_EXPOSE_TOKEN", "").lower() in ("1", "true", "yes"):
            reset_token = token
    return ForgotPasswordResponse(detail=_FORGOT_MSG, reset_token=reset_token)


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(req: ResetPasswordRequest) -> MessageResponse:
    ok, message = reset_password_with_token(req.token, req.new_password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return MessageResponse(detail=message)


@router.get("/me", response_model=UserOut)
def me(current=Depends(get_current_user)) -> UserOut:
    return UserOut(**current)


@router.put("/me", response_model=UserOut)
def update_me(req: ProfileUpdateRequest, current=Depends(get_current_user)) -> UserOut:
    #  Normaliza o CPF (so digitos) e valida com o mesmo schema do app antes de
    #  gravar. Campos ausentes (None) nao sobrescrevem o valor atual.
    data = req.model_dump(exclude_unset=True)
    if "cpf" in data and data["cpf"]:
        data["cpf"] = re.sub(r"\D", "", data["cpf"])

    try:
        ProfileUpdate(**{k: v for k, v in data.items() if v is not None})
    except Exception as e:  # ValidationError do Pydantic
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    with managed_session() as db:
        user = db.get(User, current["id"])
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado.")
        for field, value in data.items():
            setattr(user, field, value)
        db.flush()
        #  O email_hash/phone_hash sao recalculados pelo event listener de
        #  before_update; serializamos ja com os novos valores.
        result = serialize_user(user)
    return UserOut(**result)
