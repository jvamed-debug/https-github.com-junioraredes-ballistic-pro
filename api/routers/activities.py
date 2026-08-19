"""Habitualidades e competicoes, no escopo do usuario.

Registra a pratica de tiro que o CAC precisa comprovar e a conta por grupo de
equipamento + calibre — o par que a exigencia legal de frequencia observa.
Mesmo padrao de isolamento por usuario de api/routers/data.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.schemas import ActivityIn, ActivityOut, ActivitySummaryRow
from api.security import get_current_user
from core.models import Activity, Firearm, managed_session

router = APIRouter(prefix="/api/activities", tags=["habitualidades"])

_FIELDS = (
    "date", "kind", "category", "caliber", "firearm_id", "shots",
    "location", "value", "notes",
)


def _out(a: Activity) -> dict:
    return {f: getattr(a, f) for f in _FIELDS} | {"id": a.id, "image_url": a.image_url}


def _owned_or_404(db, model, obj_id: int, user_id: int):
    obj = db.get(model, obj_id)
    if obj is None or obj.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nao encontrado.")
    return obj


@router.get("", response_model=list[ActivityOut])
def list_activities(current=Depends(get_current_user)):
    with managed_session() as db:
        rows = (
            db.query(Activity)
            .filter_by(user_id=current["id"])
            .order_by(Activity.date.desc(), Activity.id.desc())
            .all()
        )
        return [_out(a) for a in rows]


@router.get("/summary", response_model=list[ActivitySummaryRow])
def summary(
    since: date | None = Query(None, description="Conta a partir desta data (inclusive)."),
    current=Depends(get_current_user),
):
    """Habitualidades contadas por grupo de equipamento + calibre.

    Com `since`, considera so as atividades a partir da data — util para medir
    a frequencia dentro do semestre corrente.
    """
    with managed_session() as db:
        q = db.query(Activity).filter_by(user_id=current["id"])
        if since is not None:
            q = q.filter(Activity.date >= since)
        agg: dict[tuple, dict] = {}
        for a in q.all():
            key = (a.category, a.caliber or "")
            row = agg.setdefault(key, {
                "category": a.category, "caliber": a.caliber,
                "count": 0, "shots": 0, "last_date": None,
            })
            row["count"] += 1
            row["shots"] += a.shots or 0
            if row["last_date"] is None or (a.date and a.date > row["last_date"]):
                row["last_date"] = a.date
    #  Mais frequentes primeiro.
    return sorted(agg.values(), key=lambda r: r["count"], reverse=True)


@router.post("", response_model=ActivityOut, status_code=status.HTTP_201_CREATED)
def create_activity(body: ActivityIn, current=Depends(get_current_user)):
    data = body.model_dump()
    data["date"] = data.get("date") or date.today()
    with managed_session() as db:
        if data.get("firearm_id") is not None:
            _owned_or_404(db, Firearm, data["firearm_id"], current["id"])
        act = Activity(user_id=current["id"], **data)
        db.add(act)
        db.flush()
        return _out(act)


@router.put("/{activity_id}", response_model=ActivityOut)
def update_activity(activity_id: int, body: ActivityIn, current=Depends(get_current_user)):
    data = body.model_dump()
    with managed_session() as db:
        act = _owned_or_404(db, Activity, activity_id, current["id"])
        if data.get("date") is None:
            data["date"] = act.date
        if data.get("firearm_id") is not None:
            _owned_or_404(db, Firearm, data["firearm_id"], current["id"])
        for k, v in data.items():
            setattr(act, k, v)
        db.flush()
        return _out(act)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(activity_id: int, current=Depends(get_current_user)):
    with managed_session() as db:
        act = _owned_or_404(db, Activity, activity_id, current["id"])
        db.delete(act)
