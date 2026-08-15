"""Aplicacao FastAPI do Ballistic Pro.

Servida por uvicorn (ver Dockerfile.api). Roda ao lado do app Streamlit; os
dois compartilham core/ e services/. O frontend React/PWA e os apps de loja
(Capacitor) consomem esta API.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import (
    advisor,
    auth,
    ballistics,
    data,
    reloading,
    reports,
    targets,
    webauthn_auth,
)

app = FastAPI(
    title="Ballistic Pro API",
    version="1.0.0",
    description="API de balistica e recarga — catalogo, trajetoria e cartao de DOPE.",
)

#  Origens liberadas para o frontend. Em producao, defina API_CORS_ORIGINS com
#  a lista separada por virgula (ex.: https://app.seudominio.com). O default
#  '*' facilita o desenvolvimento local; nao deixe assim se a API expuser
#  dados sensiveis de usuario (fase 1b em diante).
_origins = os.getenv("API_CORS_ORIGINS", "*")
allow_origins = ["*"] if _origins.strip() == "*" else [
    o.strip() for o in _origins.split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=_origins.strip() != "*",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ballistics.router)
app.include_router(auth.router)
app.include_router(data.router)
app.include_router(advisor.router)
app.include_router(reloading.router)
app.include_router(reports.router)
app.include_router(webauthn_auth.router)
app.include_router(targets.router)


@app.get("/api/health", tags=["meta"])
def health() -> dict:
    """Sonda de saude para o EasyPanel/healthcheck."""
    return {"status": "ok", "service": "ballistic-pro-api"}
