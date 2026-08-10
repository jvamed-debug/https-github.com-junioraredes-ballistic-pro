"""Consultor de recarga (IA).

Reaproveita services.ai_advisor. Por padrao roda em MODO OFFLINE (analise por
regras, sem chave nem rede) — determinístico e sempre disponivel. Se o
ambiente tiver ANTHROPIC_API_KEY ou OPENAI_API_KEY, tenta usar o LLM; o
health_check do proprio advisor derruba para offline se a chave/rede/SDK
falharem, entao a resposta nunca vira uma mensagem de erro do SDK.
"""

import os

from fastapi import APIRouter, Depends

from api.schemas import AdviceOut, LoadAdviceIn, TrendAdviceIn
from api.security import get_current_user
from services.ai_advisor import BallisticAdvisor

router = APIRouter(prefix="/api/advisor", tags=["ia"])


def _advisor() -> BallisticAdvisor:
    adv = BallisticAdvisor()
    anthropic = os.getenv("ANTHROPIC_API_KEY")
    openai = os.getenv("OPENAI_API_KEY")
    #  configure() so adota o provider se o health_check passar; caso contrario
    #  seguimos em offline.
    if anthropic:
        adv.configure("anthropic", anthropic)
    elif openai:
        adv.configure("openai", openai)
    return adv


@router.post("/load", response_model=AdviceOut)
def load_advice(body: LoadAdviceIn, _=Depends(get_current_user)) -> AdviceOut:
    r = _advisor().suggest_load(
        body.caliber,
        body.projectile or "",
        body.powder or "",
        {
            "charge": body.charge,
            "velocity": body.velocity,
            "sd": body.sd,
            "grouping": body.grouping,
        },
    )
    return AdviceOut(content=r.content, provider=r.provider, confidence=r.confidence)


@router.post("/trend", response_model=AdviceOut)
def trend_advice(body: TrendAdviceIn, _=Depends(get_current_user)) -> AdviceOut:
    r = _advisor().analyze_performance_trend([s.model_dump() for s in body.sessions])
    return AdviceOut(content=r.content, provider=r.provider, confidence=r.confidence)
