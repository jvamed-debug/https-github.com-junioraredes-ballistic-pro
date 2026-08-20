"""Locais uteis do atirador — clubes, lojas e estandes.

Lista de lugares (onde treinar, onde comprar) com endereco e, quando houver,
coordenadas. Nao ha mapa proprio: o frontend monta os links de navegacao
(Google Maps/Waze) a partir daqui. Isolado por usuario.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas import PlaceIn, PlaceOut
from api.security import get_current_user
from core.models import Place, managed_session

router = APIRouter(prefix="/api/places", tags=["locais"])

_FIELDS = ("name", "kind", "address", "city", "lat", "lng", "phone", "url", "notes")


def _out(p: Place) -> dict:
    return {f: getattr(p, f) for f in _FIELDS} | {"id": p.id}


def _owned_or_404(db, obj_id: int, user_id: int) -> Place:
    obj = db.get(Place, obj_id)
    if obj is None or obj.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nao encontrado.")
    return obj


@router.get("", response_model=list[PlaceOut])
def list_places(current=Depends(get_current_user)):
    with managed_session() as db:
        rows = (
            db.query(Place)
            .filter_by(user_id=current["id"])
            .order_by(Place.kind, Place.name)
            .all()
        )
        return [_out(p) for p in rows]


@router.post("", response_model=PlaceOut, status_code=status.HTTP_201_CREATED)
def create_place(body: PlaceIn, current=Depends(get_current_user)):
    with managed_session() as db:
        place = Place(user_id=current["id"], **body.model_dump())
        db.add(place)
        db.flush()
        return _out(place)


@router.put("/{place_id}", response_model=PlaceOut)
def update_place(place_id: int, body: PlaceIn, current=Depends(get_current_user)):
    with managed_session() as db:
        place = _owned_or_404(db, place_id, current["id"])
        for k, v in body.model_dump().items():
            setattr(place, k, v)
        db.flush()
        return _out(place)


@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_place(place_id: int, current=Depends(get_current_user)):
    with managed_session() as db:
        place = _owned_or_404(db, place_id, current["id"])
        db.delete(place)
