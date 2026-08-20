"""Dados do usuario: inventario, armas e logbook (sessoes de recarga).

Tudo protegido por JWT e estritamente no escopo do usuario autenticado —
cada consulta filtra por user_id, e alterar/apagar um registro de outro dono
responde 404 (nao vaza a existencia do recurso alheio).
"""

from datetime import date
from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas import (
    FirearmAlert,
    FirearmIn,
    FirearmOut,
    InventoryIn,
    InventoryOut,
    LogbookCreateOut,
    LogbookIn,
    LogbookOut,
)
from api.security import get_current_user
from core.models import Firearm, InventoryItem, ReloadSession, managed_session
from services.reloading_service import ReloadingService

router = APIRouter(prefix="/api", tags=["dados"])


# --------------------------- serializadores -------------------------------


def _inv_out(i: InventoryItem) -> dict:
    return {
        "id": i.id,
        "category": i.category,
        "name": i.name,
        "quantity": i.quantity,
        "unit": i.unit,
        "price_unit": i.price_unit or 0.0,
        "batch_number": i.batch_number,
        "expiration_date": i.expiration_date,
    }


def _gun_out(f: Firearm) -> dict:
    #  Campos cifrados (serial/sigma/craf) sao lidos DENTRO da sessao.
    return {
        "id": f.id,
        "model": f.model,
        "serial": f.serial,
        "sigma": f.sigma,
        "craf": f.craf,
        "expiration": f.expiration,
        "image_url": f.image_url,
        "collection": f.collection or "pessoal",
        "gts": f.gts,
        "gts_expiration": f.gts_expiration,
        "craf_doc_url": f.craf_doc_url,
        "gts_doc_url": f.gts_doc_url,
    }


def _log_out(s: ReloadSession) -> dict:
    return {
        "id": s.id,
        "caliber": s.caliber,
        "date": s.date,
        "quantity": s.quantity,
        "projectile": s.projectile,
        "powder": s.powder,
        "charge": s.charge,
        "primer": s.primer,
        "case": s.case,
        "velocity_avg": s.velocity_avg,
        "velocity_sd": s.velocity_sd,
        "grouping_mm": s.grouping_mm,
        "firearm_id": s.firearm_id,
        "notes": s.notes,
    }


def _owned_or_404(db, model, obj_id: int, user_id: int):
    obj = db.get(model, obj_id)
    if obj is None or obj.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nao encontrado.")
    return obj


# ------------------------------ inventario --------------------------------


@router.get("/inventory", response_model=list[InventoryOut])
def list_inventory(current=Depends(get_current_user)):
    with managed_session() as db:
        rows = db.query(InventoryItem).filter_by(user_id=current["id"]).all()
        return [_inv_out(i) for i in rows]


@router.post("/inventory", response_model=InventoryOut, status_code=status.HTTP_201_CREATED)
def create_inventory(body: InventoryIn, current=Depends(get_current_user)):
    with managed_session() as db:
        item = InventoryItem(user_id=current["id"], **body.model_dump())
        db.add(item)
        db.flush()
        return _inv_out(item)


@router.put("/inventory/{item_id}", response_model=InventoryOut)
def update_inventory(item_id: int, body: InventoryIn, current=Depends(get_current_user)):
    with managed_session() as db:
        item = _owned_or_404(db, InventoryItem, item_id, current["id"])
        for k, v in body.model_dump().items():
            setattr(item, k, v)
        db.flush()
        return _inv_out(item)


@router.delete("/inventory/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory(item_id: int, current=Depends(get_current_user)):
    with managed_session() as db:
        item = _owned_or_404(db, InventoryItem, item_id, current["id"])
        db.delete(item)


# -------------------------------- armas -----------------------------------


@router.get("/firearms", response_model=list[FirearmOut])
def list_firearms(current=Depends(get_current_user)):
    with managed_session() as db:
        rows = db.query(Firearm).filter_by(user_id=current["id"]).all()
        return [_gun_out(f) for f in rows]


@router.post("/firearms", response_model=FirearmOut, status_code=status.HTTP_201_CREATED)
def create_firearm(body: FirearmIn, current=Depends(get_current_user)):
    with managed_session() as db:
        gun = Firearm(user_id=current["id"], **body.model_dump())
        db.add(gun)
        db.flush()
        return _gun_out(gun)


@router.put("/firearms/{gun_id}", response_model=FirearmOut)
def update_firearm(gun_id: int, body: FirearmIn, current=Depends(get_current_user)):
    with managed_session() as db:
        gun = _owned_or_404(db, Firearm, gun_id, current["id"])
        for k, v in body.model_dump().items():
            setattr(gun, k, v)
        db.flush()
        return _gun_out(gun)


@router.delete("/firearms/{gun_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_firearm(gun_id: int, current=Depends(get_current_user)):
    with managed_session() as db:
        gun = _owned_or_404(db, Firearm, gun_id, current["id"])
        db.delete(gun)


@router.get("/firearms/alerts", response_model=list[FirearmAlert])
def firearm_alerts(days: int = 60, current=Depends(get_current_user)):
    """Documentos (CRAF/GTS) do acervo vencidos ou vencendo em ate `days` dias.

    Ordenados do mais urgente (mais vencido) ao menos. `days_left` negativo
    indica documento ja vencido.
    """
    today = date.today()
    with managed_session() as db:
        rows = db.query(Firearm).filter_by(user_id=current["id"]).all()
        alerts: list[FirearmAlert] = []
        for f in rows:
            for doc, exp in (("CRAF", f.expiration), ("GTS", f.gts_expiration)):
                if exp is None:
                    continue
                days_left = (exp - today).days
                if days_left <= days:
                    alerts.append(FirearmAlert(
                        firearm_id=f.id,
                        model=f.model,
                        doc=doc,
                        expiration=exp,
                        days_left=days_left,
                        collection=f.collection or "pessoal",
                    ))
    alerts.sort(key=lambda a: a.days_left)
    return alerts


# ------------------------------- logbook ----------------------------------


@router.get("/logbook", response_model=list[LogbookOut])
def list_logbook(current=Depends(get_current_user)):
    with managed_session() as db:
        rows = (
            db.query(ReloadSession)
            .filter_by(user_id=current["id"])
            .order_by(ReloadSession.date.desc())
            .all()
        )
        return [_log_out(s) for s in rows]


@router.post("/logbook", response_model=LogbookCreateOut, status_code=status.HTTP_201_CREATED)
def create_logbook(
    body: LogbookIn, deduct: bool = False, current=Depends(get_current_user)
):
    """Registra uma sessao de recarga.

    Com `deduct=true`, depois de gravar debita os insumos correspondentes do
    estoque (polvora pela carga x quantidade; projetil/espoleta/estojo 1-a-1)
    e devolve o custo unitario estimado — o mesmo comportamento do app
    Streamlit. A deducao roda apos o commit da sessao, para nunca baixar
    estoque de uma gravacao que falhou.
    """
    data = body.model_dump()
    data["date"] = data.get("date") or date.today()
    with managed_session() as db:
        #  Se veio firearm_id, ela precisa ser do proprio usuario.
        if data.get("firearm_id") is not None:
            _owned_or_404(db, Firearm, data["firearm_id"], current["id"])
        session = ReloadSession(user_id=current["id"], **data)
        db.add(session)
        db.flush()
        out = _log_out(session)

    #  Fora do bloco: a sessao ja esta commitada. So agora mexemos no estoque.
    out["deductions"] = []
    out["unit_cost"] = None
    if deduct:
        sess = SimpleNamespace(
            powder=data.get("powder"),
            charge=data.get("charge"),
            quantity=data.get("quantity"),
            projectile=data.get("projectile"),
            primer=data.get("primer"),
            case=data.get("case"),
        )
        _, out["deductions"] = ReloadingService.deduct_inventory(sess, current["id"])
        if data.get("powder") and data.get("charge"):
            out["unit_cost"] = ReloadingService.calculate_unit_cost(sess, current["id"])
    return out


@router.put("/logbook/{session_id}", response_model=LogbookOut)
def update_logbook(session_id: int, body: LogbookIn, current=Depends(get_current_user)):
    data = body.model_dump()
    with managed_session() as db:
        session = _owned_or_404(db, ReloadSession, session_id, current["id"])
        #  Data ausente na edicao mantem a original.
        if data.get("date") is None:
            data["date"] = session.date
        #  firearm_id, se informado, precisa ser do proprio usuario.
        if data.get("firearm_id") is not None:
            _owned_or_404(db, Firearm, data["firearm_id"], current["id"])
        for k, v in data.items():
            setattr(session, k, v)
        db.flush()
        return _log_out(session)


@router.delete("/logbook/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_logbook(session_id: int, current=Depends(get_current_user)):
    with managed_session() as db:
        session = _owned_or_404(db, ReloadSession, session_id, current["id"])
        db.delete(session)
