"""Analise de alvo por foto (visao computacional).

Recebe a foto do alvo, detecta os impactos, agrupa-os e mede o agrupamento
(reusa cv_utils.calculate_group_size_v2, o mesmo motor do app Streamlit). Dois
endpoints, ambos autenticados e sem estado:

    POST /api/targets/analyze  -> metricas + imagem anotada (PNG base64)
    POST /api/targets/report   -> PDF do relatorio de performance

cv2/PIL sao pesados e ficam em import tardio, para nao pesar no boot da API.
"""

from __future__ import annotations

import base64
import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from api.security import get_current_user

router = APIRouter(prefix="/api/targets", tags=["alvo"])

#  Limite de tamanho do upload (8 MB) — foto de celular cabe folgado.
_MAX_BYTES = 8 * 1024 * 1024


async def _read_image(file: UploadFile):
    from PIL import Image

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")
    if len(data) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="Imagem muito grande (max 8 MB).")
    try:
        return Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Imagem invalida.")


def _analyze(image, target_width_mm, sensitivity, center_x, center_y):
    from cv_utils import calculate_group_size_v2

    center = None
    if center_x is not None and center_y is not None:
        center = (center_x, center_y)
    return calculate_group_size_v2(
        image,
        target_width_mm=target_width_mm,
        sensitivity=sensitivity,
        center_point=center,
    )


def _serialize(results: dict) -> dict:
    import cv2

    ann = results["annotated_image"]
    #  cv_utils desenha sobre um array RGB; imencode espera BGR — converte para
    #  o PNG sair com as cores certas.
    bgr = cv2.cvtColor(ann, cv2.COLOR_RGB2BGR) if ann.ndim == 3 else ann
    ok, buf = cv2.imencode(".png", bgr)
    b64 = base64.b64encode(buf.tobytes()).decode() if ok else ""
    return {
        "shot_count": int(results["shot_count"]),
        "pixel_per_mm": float(results["pixel_per_mm"]),
        "groups": [
            {
                "id": g["id"],
                "shots": [[int(s[0]), int(s[1])] for s in g["shots"]],
                "group_size_mm": round(float(g["group_size_mm"]), 2),
                "poi_mm": [round(float(g["poi_mm"][0]), 1), round(float(g["poi_mm"][1]), 1)],
            }
            for g in results["groups"]
        ],
        "annotated_image": f"data:image/png;base64,{b64}",
    }


@router.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    target_width_mm: float = Form(210.0),
    sensitivity: int = Form(155),
    center_x: int | None = Form(None),
    center_y: int | None = Form(None),
    current=Depends(get_current_user),
) -> dict:
    """Detecta impactos e mede o agrupamento; devolve a imagem anotada."""
    image = await _read_image(file)
    results = _analyze(image, target_width_mm, sensitivity, center_x, center_y)
    return _serialize(results)


@router.post("/report")
async def report(
    file: UploadFile = File(...),
    target_width_mm: float = Form(210.0),
    sensitivity: int = Form(155),
    center_x: int | None = Form(None),
    center_y: int | None = Form(None),
    current=Depends(get_current_user),
) -> Response:
    """Gera o PDF do relatorio de performance com a imagem analisada."""
    import cv2

    from report_gen import create_performance_report_v2

    image = await _read_image(file)
    results = _analyze(image, target_width_mm, sensitivity, center_x, center_y)
    if not results["groups"]:
        raise HTTPException(status_code=422, detail="Nenhum impacto detectado para o relatorio.")

    #  O relatorio codifica a imagem por conta propria e espera BGR.
    results_for_pdf = dict(results)
    results_for_pdf["annotated_image"] = cv2.cvtColor(results["annotated_image"], cv2.COLOR_RGB2BGR)
    pdf_bytes = create_performance_report_v2(current, results_for_pdf, None)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="relatorio_performance.pdf"'},
    )
