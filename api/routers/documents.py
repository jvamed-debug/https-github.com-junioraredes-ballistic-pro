"""Documentos do CAC — pastas/categorias, validade e lembretes de renovacao.

Guarda os papeis que nao pertencem a uma arma (CR, filiacao, apostilamentos,
laudos, comprovantes). Cada documento tem sua propria antecedencia de lembrete
(`remind_days`): o alerta dispara quando faltam `remind_days` ou menos para
vencer — ou quando ja venceu. Tudo isolado por usuario.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status

from api.schemas import DocumentAlert, DocumentIn, DocumentOut, DocumentUploadOut
from api.security import get_current_user
from core.models import Document, managed_session
from services.doc_extraction import extract_fields

router = APIRouter(prefix="/api", tags=["documentos"])

#  Limite de tamanho do PDF enviado (8 MB) — documentos de CAC sao pequenos.
_MAX_FILE_BYTES = 8 * 1024 * 1024


def _doc_out(d: Document) -> dict:
    #  number e cifrado no banco; lido claro dentro da sessao. Os bytes do
    #  arquivo nunca vao na listagem — so o nome e um flag; baixa-se a parte.
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
        "has_file": d.file_data is not None,
        "file_name": d.file_name,
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


@router.post("/documents/upload", response_model=DocumentUploadOut,
             status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile, current=Depends(get_current_user)):
    """Recebe um PDF, le os dados (numero/validade/tipo) e cria a etiqueta.

    O arquivo fica guardado e os campos vem pre-preenchidos pela leitura
    automatica (IA quando ha chave, senao heuristica). O usuario revisa e
    ajusta depois pelo PUT — nada e cravado sem poder corrigir.
    """
    if (file.content_type or "") not in ("application/pdf", "application/octet-stream") \
            and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Envie um arquivo PDF.")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo vazio.")
    if len(data) > _MAX_FILE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="PDF acima de 8 MB.")

    fields = extract_fields(data)
    with managed_session() as db:
        doc = Document(
            user_id=current["id"],
            folder=fields.get("folder") or "Geral",
            title=fields.get("title") or (file.filename or "Documento"),
            number=fields.get("number"),
            issue_date=date.fromisoformat(fields["issue_date"]) if fields.get("issue_date") else None,
            expiration=date.fromisoformat(fields["expiration"]) if fields.get("expiration") else None,
            remind_days=30,
            file_name=file.filename,
            file_mime="application/pdf",
            file_data=data,
        )
        db.add(doc)
        db.flush()
        out = _doc_out(doc)
    out["extraction_source"] = fields.get("source", "vazio")
    return out


@router.get("/documents/{doc_id}/file")
def download_document_file(doc_id: int, current=Depends(get_current_user)):
    with managed_session() as db:
        doc = _owned_or_404(db, doc_id, current["id"])
        if doc.file_data is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sem arquivo.")
        data = bytes(doc.file_data)
        name = doc.file_name or f"documento-{doc.id}.pdf"
        mime = doc.file_mime or "application/pdf"
    return Response(
        content=data,
        media_type=mime,
        headers={"Content-Disposition": f'inline; filename="{name}"'},
    )


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
