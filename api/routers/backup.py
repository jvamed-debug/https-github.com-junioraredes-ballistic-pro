"""Backup local: exporta todos os dados do usuario em um unico JSON.

O usuario baixa um arquivo com o proprio acervo — armas, documentos (metadados,
sem o PDF em si), inventario, habitualidades, eventos, locais, cartoes de DOPE e
sessoes de recarga. Serve de copia de seguranca offline (o backup no Google
Drive, que depende de OAuth, fica para quando houver essa integracao).

Atencao: o arquivo traz dados sensiveis em claro (numeros de serie, CRAF, GTS,
CPF...), porque um backup cifrado com a chave DESTE servidor seria inutil fora
dele. Vai protegido por JWT e so com os dados do proprio usuario.
"""

from datetime import date, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from api.security import get_current_user
from core.models import (
    Activity,
    Document,
    DopeCard,
    Event,
    Firearm,
    InventoryItem,
    Place,
    ReloadSession,
    User,
    managed_session,
)

router = APIRouter(prefix="/api/backup", tags=["backup"])

#  Modelos exportados (rótulo no JSON -> classe). Ordem estável para diffs.
_EXPORTED = [
    ("firearms", Firearm),
    ("inventory", InventoryItem),
    ("logbook", ReloadSession),
    ("activities", Activity),
    ("documents", Document),
    ("events", Event),
    ("places", Place),
    ("dope_cards", DopeCard),
]

#  Colunas nunca exportadas: bytes de arquivo (pesados/binários) e o vínculo de
#  dono (redundante — o backup já é de um usuário só).
_SKIP_COLS = {"file_data", "user_id"}


def _serialize(obj) -> dict:
    out: dict = {}
    for col in obj.__table__.columns:
        if col.name in _SKIP_COLS:
            continue
        val = getattr(obj, col.name)
        if isinstance(val, (date, datetime)):
            val = val.isoformat()
        elif isinstance(val, (bytes, bytearray, memoryview)):
            continue  # nunca serializa binário
        out[col.name] = val
    return out


@router.get("/export")
def export_backup(current=Depends(get_current_user)):
    """Baixa um JSON com todos os dados do usuário autenticado."""
    with managed_session() as db:
        user = db.get(User, current["id"])
        profile = {
            "username": user.username,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "cpf": user.cpf,
            "cr_number": user.cr_number,
            "cr_expiration": user.cr_expiration.isoformat() if user.cr_expiration else None,
        }
        data: dict = {
            "version": 1,
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "profile": profile,
        }
        counts: dict = {}
        for label, model in _EXPORTED:
            rows = db.query(model).filter_by(user_id=current["id"]).all()
            data[label] = [_serialize(r) for r in rows]
            counts[label] = len(rows)
        data["counts"] = counts

    fname = f"ballistic-pro-backup-{date.today().isoformat()}.json"
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
