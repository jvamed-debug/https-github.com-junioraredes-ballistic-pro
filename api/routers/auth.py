"""Endpoints de autenticacao e perfil.

Toda a logica sensivel (verificacao de senha, unicidade por blind index,
bloqueio de forca-bruta, recuperacao anti-enumeracao) ja vive em core.auth e e
reaproveitada aqui — a API so acrescenta a emissao/validacao do token JWT.
"""

import re

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas import (
    LoginRequest,
    MessageResponse,
    ProfileUpdateRequest,
    RecoverRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from api.security import create_access_token, get_current_user, serialize_user
from core.auth import (
    authenticate,
    clear_login_attempts,
    login_lock_remaining,
    record_failed_login,
    recover_password,
    register_user,
)
from core.models import User, managed_session
from schemas import ProfileUpdate

router = APIRouter(prefix="/api/auth", tags=["auth"])


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
