"""Agenda de eventos e competicoes de tiro, no escopo do usuario.

Uma agenda simples do que vem por ai — competicoes, cursos, provas de nivel —
com data e local, para nao perder inscricao. Isolada por usuario, no mesmo
padrao dos demais recursos.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.schemas import EventIn, EventOut
from api.security import get_current_user
from core.models import Event, managed_session

router = APIRouter(prefix="/api/events", tags=["eventos"])

_FIELDS = ("title", "date", "kind", "location", "url", "notes")


def _out(e: Event) -> dict:
    return {f: getattr(e, f) for f in _FIELDS} | {"id": e.id}


def _owned_or_404(db, obj_id: int, user_id: int) -> Event:
    obj = db.get(Event, obj_id)
    if obj is None or obj.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nao encontrado.")
    return obj


@router.get("", response_model=list[EventOut])
def list_events(
    upcoming: bool = Query(False, description="So eventos de hoje em diante."),
    current=Depends(get_current_user),
):
    """Eventos do usuario, dos mais proximos aos mais distantes.

    Com `upcoming=true`, retorna so os de hoje em diante (agenda do que vem).
    """
    with managed_session() as db:
        q = db.query(Event).filter_by(user_id=current["id"])
        if upcoming:
            q = q.filter(Event.date >= date.today())
        rows = q.order_by(Event.date.asc(), Event.id.asc()).all()
        return [_out(e) for e in rows]


@router.post("", response_model=EventOut, status_code=status.HTTP_201_CREATED)
def create_event(body: EventIn, current=Depends(get_current_user)):
    with managed_session() as db:
        ev = Event(user_id=current["id"], **body.model_dump())
        db.add(ev)
        db.flush()
        return _out(ev)


@router.put("/{event_id}", response_model=EventOut)
def update_event(event_id: int, body: EventIn, current=Depends(get_current_user)):
    with managed_session() as db:
        ev = _owned_or_404(db, event_id, current["id"])
        for k, v in body.model_dump().items():
            setattr(ev, k, v)
        db.flush()
        return _out(ev)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, current=Depends(get_current_user)):
    with managed_session() as db:
        ev = _owned_or_404(db, event_id, current["id"])
        db.delete(ev)
