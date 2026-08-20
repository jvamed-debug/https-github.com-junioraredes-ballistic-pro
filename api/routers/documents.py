"""Documentos do CAC — pastas/categorias, validade e lembretes de renovacao.

Guarda os papeis que nao pertencem a uma arma (CR, filiacao, apostilamentos,
laudos, comprovantes). Cada documento tem sua propria antecedencia de lembrete
(`remind_days`): o alerta dispara quando faltam `remind_days` ou menos para
vencer — ou quando ja venceu. Tudo isolado por usuario.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status

from api.schemas import DocumentAlert, DocumentIn, DocumentOut
from api.security import get_current_user
from core.models import Document, managed_session

router = APIRouter(prefix="/api", tags=["documentos"])


def _doc_out(d: Document) -> dict:
    #  number e cifrado no banco; lido claro dentro da sessao.
    return {
        "id": d.id,
        "folder": d.folder or "Geral",
        "title": d.title,
        "number": d.number,
        "issue_date": d.issue_date,
        "expiration": d.expiration,
        "remind_days": d.remind_days if d.remind_days is not None else 30,
        "file_url": d.file_url,
        "notes": d.notes,
    }


def _owned_or_404(db, obj_id: int, user_id: int) -> Document:
    obj = db.get(Document, obj_id)
    if obj is None or obj.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nao encontrado.")
    return obj


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(current=Depends(get_current_user)):
    with managed_session() as db:
        rows = (
            db.query(Document)
            .filter_by(user_id=current["id"])
            .order_by(Document.folder, Document.title)
            .all()
        )
        return [_doc_out(d) for d in rows]


@router.get("/documents/alerts", response_model=list[DocumentAlert])
def document_alerts(current=Depends(get_current_user)):
    """Documentos vencidos ou dentro da propria antecedencia de lembrete."""
    today = date.today()
    with managed_session() as db:
        rows = db.query(Document).filter_by(user_id=current["id"]).all()
        alerts: list[DocumentAlert] = []
        for d in rows:
            if d.expiration is None:
                continue
            days_left = (d.expiration - today).days
            window = d.remind_days if d.remind_days is not None else 30
            if days_left <= window:
                alerts.append(DocumentAlert(
                    document_id=d.id,
                    title=d.title,
                    folder=d.folder or "Geral",
                    expiration=d.expiration,
                    days_left=days_left,
                ))
    alerts.sort(key=lambda a: a.days_left)
    return alerts


@router.post("/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def create_document(body: DocumentIn, current=Depends(get_current_user)):
    with managed_session() as db:
        doc = Document(user_id=current["id"], **body.model_dump())
        db.add(doc)
        db.flush()
        return _doc_out(doc)


@router.put("/documents/{doc_id}", response_model=DocumentOut)
def update_document(doc_id: int, body: DocumentIn, current=Depends(get_current_user)):
    with managed_session() as db:
        doc = _owned_or_404(db, doc_id, current["id"])
        for k, v in body.model_dump().items():
            setattr(doc, k, v)
        db.flush()
        return _doc_out(doc)


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(doc_id: int, current=Depends(get_current_user)):
    with managed_session() as db:
        doc = _owned_or_404(db, doc_id, current["id"])
        db.delete(doc)
