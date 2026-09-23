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

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import Date, DateTime

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
#  Firearms vem primeiro de proposito: no import, as referencias firearm_id de
#  logbook/activities/dope_cards sao remapeadas para os ids recem-criados.
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

#  Modelos filhos: apontam para uma arma. No import, o firearm_id do backup é
#  traduzido para o id novo (ou o da arma duplicada já existente); se não houver
#  correspondência, entra como nulo (o vínculo é sempre opcional).
_FIREARM_CHILDREN = {"logbook", "activities", "dope_cards"}

#  Assinatura de deduplicação por modelo: as colunas de negócio que, iguais,
#  indicam a mesma linha. Best-effort — evita reimportar o mesmo backup duas
#  vezes sem depender de id. EncryptedString compara em texto claro (o getattr
#  já decifra), então serial/CRAF/número entram na conta.
_SIGNATURE = {
    "firearms": ("model", "serial", "craf", "gts"),
    "inventory": ("category", "name", "batch_number"),
    "logbook": ("date", "caliber", "projectile", "powder", "charge", "quantity"),
    "activities": ("date", "kind", "category", "caliber", "shots"),
    "documents": ("folder", "title", "number"),
    "events": ("title", "date", "kind"),
    "places": ("name", "kind", "city"),
    "dope_cards": ("name", "weight_grains", "muzzle_velocity_fps"),
}

#  Campos de perfil preenchidos no import APENAS quando o campo do usuário atual
#  está vazio — nunca sobrescreve o que já existe. username e email ficam de
#  fora (identidade + unicidade por blind index).
_PROFILE_FILL = ("name", "cpf", "phone", "cr_number", "cr_expiration", "address_acervo")


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


def _coerce(model, row: dict) -> dict:
    """Devolve só as colunas conhecidas do modelo (menos id/user_id/binário),
    convertendo strings ISO de volta para date/datetime conforme o tipo real da
    coluna. Chaves desconhecidas no JSON são ignoradas (tolerante a versões)."""
    out: dict = {}
    for col in model.__table__.columns:
        name = col.name
        if name in _SKIP_COLS or name == "id" or name not in row:
            continue
        val = row[name]
        if isinstance(val, str) and val:
            if isinstance(col.type, DateTime):
                try:
                    val = datetime.fromisoformat(val.replace("Z", ""))
                except ValueError:
                    val = None
            elif isinstance(col.type, Date):
                try:
                    val = date.fromisoformat(val[:10])
                except ValueError:
                    val = None
        out[name] = val
    return out


def _signature(label: str, obj) -> tuple:
    """Chave natural de uma linha (via atributos já decifrados) para dedup."""
    return tuple(getattr(obj, f, None) for f in _SIGNATURE[label])


@router.post("/import")
def import_backup(payload: dict = Body(...), current=Depends(get_current_user)):
    """Restaura um JSON de backup na conta autenticada.

    Aditivo e idempotente: as linhas entram como novas (ids atribuídos pelo
    banco, sempre com o user_id do dono atual), e linhas equivalentes às já
    existentes são puladas — reimportar o mesmo arquivo não duplica nada. As
    referências de arma (firearm_id) são remapeadas para os ids recém-criados.
    O perfil só é completado nos campos ainda vazios; nada é sobrescrito.
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Backup inválido: JSON esperado.")
    if payload.get("version") != 1:
        raise HTTPException(
            status_code=400,
            detail=f"Versão de backup não suportada: {payload.get('version')!r} (esperado 1).",
        )

    uid = current["id"]
    imported: dict = {}
    skipped: dict = {}

    with managed_session() as db:
        #  Remapeia firearm_id do backup -> id no banco (arma nova ou a duplicada
        #  já existente). Preenchido ao processar 'firearms', consumido pelos
        #  modelos filhos.
        firearm_map: dict = {}

        for label, model in _EXPORTED:
            rows = payload.get(label) or []
            if not isinstance(rows, list):
                raise HTTPException(status_code=400, detail=f"Campo '{label}' deve ser uma lista.")

            #  Assinaturas das linhas já existentes do usuário (dedup). Para
            #  armas, guarda também o id existente (destino do remapeamento).
            existing = db.query(model).filter_by(user_id=uid).all()
            seen: dict = {}
            for e in existing:
                seen.setdefault(_signature(label, e), e.id)

            imported[label] = 0
            skipped[label] = 0

            for raw in rows:
                if not isinstance(raw, dict):
                    skipped[label] += 1
                    continue
                old_id = raw.get("id")
                obj = model(**_coerce(model, raw))
                obj.user_id = uid

                #  Remapeia o vínculo de arma antes de gravar/dedup.
                if label in _FIREARM_CHILDREN:
                    obj.firearm_id = firearm_map.get(raw.get("firearm_id"))

                sig = _signature(label, obj)
                if sig in seen:
                    if label == "firearms" and old_id is not None:
                        firearm_map[old_id] = seen[sig]
                    skipped[label] += 1
                    continue

                db.add(obj)
                db.flush()  # atribui o id novo
                seen[sig] = obj.id
                if label == "firearms" and old_id is not None:
                    firearm_map[old_id] = obj.id
                imported[label] += 1

        #  Perfil: completa só os campos ainda vazios (nunca sobrescreve).
        profile = payload.get("profile") or {}
        profile_filled = []
        if isinstance(profile, dict):
            user = db.get(User, uid)
            for field in _PROFILE_FILL:
                incoming = profile.get(field)
                if incoming and not getattr(user, field, None):
                    if field == "cr_expiration" and isinstance(incoming, str):
                        try:
                            incoming = date.fromisoformat(incoming[:10])
                        except ValueError:
                            continue
                    setattr(user, field, incoming)
                    profile_filled.append(field)

    return {
        "imported": imported,
        "skipped": skipped,
        "profile_filled": profile_filled,
        "total_imported": sum(imported.values()),
    }
