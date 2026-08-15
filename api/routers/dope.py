"""Cartoes de DOPE salvos, no escopo do usuario.

Persistem a receita de tiro (projetil + arma + zero + torre) para o atirador
reabrir depois, opcionalmente vinculada a uma arma cadastrada. Mesmo padrao de
isolamento por usuario de api/routers/data: alterar/apagar cartao alheio da 404.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas import DopeCardIn, DopeCardOut
from api.security import get_current_user
from core.models import DopeCard, Firearm, managed_session

router = APIRouter(prefix="/api/dope-cards", tags=["dope"])

_FIELDS = (
    "name", "firearm_id", "weight_grains", "bc_g1", "muzzle_velocity_fps",
    "diameter_mm", "bullet_length_in", "zero_range_m", "max_range_m", "step_m",
    "sight_height_cm", "twist_rate_in", "twist_dir", "unit", "click_value",
)


def _out(c: DopeCard) -> dict:
    return {f: getattr(c, f) for f in _FIELDS} | {"id": c.id}


def _owned_or_404(db, model, obj_id: int, user_id: int):
    obj = db.get(model, obj_id)
    if obj is None or obj.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nao encontrado.")
    return obj


def _check_firearm(db, firearm_id, user_id):
    if firearm_id is not None:
        _owned_or_404(db, Firearm, firearm_id, user_id)


@router.get("", response_model=list[DopeCardOut])
def list_cards(current=Depends(get_current_user)):
    with managed_session() as db:
        rows = (
            db.query(DopeCard)
            .filter_by(user_id=current["id"])
            .order_by(DopeCard.created_at.desc())
            .all()
        )
        return [_out(c) for c in rows]


@router.post("", response_model=DopeCardOut, status_code=status.HTTP_201_CREATED)
def create_card(body: DopeCardIn, current=Depends(get_current_user)):
    data = body.model_dump()
    with managed_session() as db:
        _check_firearm(db, data.get("firearm_id"), current["id"])
        card = DopeCard(user_id=current["id"], **data)
        db.add(card)
        db.flush()
        return _out(card)


@router.put("/{card_id}", response_model=DopeCardOut)
def update_card(card_id: int, body: DopeCardIn, current=Depends(get_current_user)):
    data = body.model_dump()
    with managed_session() as db:
        card = _owned_or_404(db, DopeCard, card_id, current["id"])
        _check_firearm(db, data.get("firearm_id"), current["id"])
        for k, v in data.items():
            setattr(card, k, v)
        db.flush()
        return _out(card)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: int, current=Depends(get_current_user)):
    with managed_session() as db:
        card = _owned_or_404(db, DopeCard, card_id, current["id"])
        db.delete(card)
