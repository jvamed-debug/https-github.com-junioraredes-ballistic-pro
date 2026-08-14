"""Geracao de PDFs: etiqueta da caixa de municao e relatorio de acervo.

Reexpoe para o app web o que o Streamlit gerava com label_gen/report_gen. Os
geradores vivem na raiz do projeto e sao compartilhados; report_gen importa
cv2 no topo, entao ele e carregado sob demanda (lazy import) para nao pesar no
boot da API nem acoplar o relatorio de acervo ao OpenCV.

Tudo protegido por JWT e no escopo do usuario: a etiqueta so sai para uma
sessao do proprio dono (404 caso contrario), e o relatorio usa apenas os
dados do usuario autenticado.
"""

from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from api.security import get_current_user
from core.models import Firearm, ReloadSession, managed_session

router = APIRouter(prefix="/api", tags=["relatorios"])


def _pdf_response(data: bytes, filename: str) -> Response:
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _slug(value: str | None) -> str:
    """Nome de arquivo seguro: so alfanumerico, resto vira '_'."""
    raw = str(value or "arquivo")
    return "".join(c if c.isalnum() else "_" for c in raw).strip("_") or "arquivo"


@router.get("/logbook/{session_id}/label")
def logbook_label(session_id: int, current=Depends(get_current_user)):
    """PDF de etiqueta (100x60mm) para a caixa de municao de uma sessao."""
    from label_gen import create_label_pdf

    with managed_session() as db:
        s = db.get(ReloadSession, session_id)
        if s is None or s.user_id != current["id"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nao encontrado.")
        #  Snapshot dentro da sessao: apos o detach os atributos somem.
        snap = SimpleNamespace(
            date=s.date,
            caliber=s.caliber,
            projectile=s.projectile,
            powder=s.powder,
            charge=s.charge,
            quantity=s.quantity,
            primer=s.primer,
            case=s.case,
            velocity_avg=s.velocity_avg,
            notes=s.notes,
        )

    pdf = create_label_pdf(snap, current.get("name") or current["username"])
    return _pdf_response(pdf.getvalue(), f"etiqueta_{_slug(snap.caliber)}_{session_id}.pdf")


@router.get("/reports/inspection")
def inspection_report(current=Depends(get_current_user)):
    """PDF de acervo e atividades (dados do CAC, armas e ultimas sessoes)."""
    from report_gen import create_inspection_report

    with managed_session() as db:
        guns = db.query(Firearm).filter_by(user_id=current["id"]).all()
        firearms_data = [
            {"model": g.model, "serial": g.serial, "sigma": g.sigma, "craf": g.craf}
            for g in guns
        ]
        sessions = (
            db.query(ReloadSession)
            .filter_by(user_id=current["id"])
            .order_by(ReloadSession.date.desc())
            .all()
        )
        sessions_data = [
            {
                #  "date" (ISO) so para ordenar; "date_str" e o que o PDF imprime.
                "date": s.date.isoformat() if s.date else "",
                "date_str": s.date.strftime("%d/%m/%Y") if s.date else "N/A",
                "caliber": s.caliber,
                "charge": s.charge or 0,
                "quantity": s.quantity or 0,
            }
            for s in sessions
        ]

    pdf_bytes = create_inspection_report(current, firearms_data, sessions_data)
    return _pdf_response(pdf_bytes, "relatorio_acervo.pdf")
