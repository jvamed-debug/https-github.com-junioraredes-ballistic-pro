"""Nivel do atirador — progresso gamificado a partir das habitualidades.

Deriva um nivel/titulo do total de atividades registradas (services nao
guardam nada novo: le a tabela Activity). Estimula a frequencia sem inventar
metrica — o que conta e a pratica que o proprio usuario registrou.
"""

from fastapi import APIRouter, Depends

from api.schemas import LevelOut
from api.security import get_current_user
from core.models import Activity, managed_session

router = APIRouter(prefix="/api", tags=["nivel"])

#  Faixas por total de habitualidades: (limiar, titulo). Ordem crescente.
_TIERS = [
    (0, "Novato"),
    (5, "Iniciante"),
    (15, "Praticante"),
    (30, "Habitual"),
    (60, "Atirador Assíduo"),
    (120, "Veterano"),
    (240, "Mestre"),
]


def compute_level(total: int) -> dict:
    """Nivel, titulo e progresso rumo ao proximo, para um total de atividades."""
    idx = 0
    for i, (threshold, _) in enumerate(_TIERS):
        if total >= threshold:
            idx = i
    current_min, title = _TIERS[idx]
    if idx + 1 < len(_TIERS):
        next_min, next_title = _TIERS[idx + 1]
        span = next_min - current_min
        progress = (total - current_min) / span if span > 0 else 1.0
    else:
        next_min, next_title, progress = None, None, 1.0
    return {
        "level": idx + 1,
        "title": title,
        "current_min": current_min,
        "next_min": next_min,
        "next_title": next_title,
        "progress": round(min(max(progress, 0.0), 1.0), 3),
    }


@router.get("/level", response_model=LevelOut)
def level(current=Depends(get_current_user)) -> LevelOut:
    with managed_session() as db:
        rows = db.query(Activity).filter_by(user_id=current["id"]).all()
        total = len(rows)
        shots = sum(a.shots or 0 for a in rows)
        competitions = sum(1 for a in rows if a.kind == "competicao")
        categories = len({(a.category, a.caliber or "") for a in rows})

    data = compute_level(total)
    return LevelOut(
        total_activities=total,
        total_shots=shots,
        competitions=competitions,
        categories=categories,
        **data,
    )
