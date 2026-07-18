from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape as xml_escape
import cv2
import io
import os


def _get(obj, key, default=""):
    """Helper: acessa dados de dict ou objeto ORM de forma transparente."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _safe(value):
    """Escape user content for safe embedding in ReportLab Paragraphs."""
    return xml_escape(str(value)) if value else ""


def create_inspection_report(user_data, firearms_data=None, sessions_data=None):
    """
    Gera relatório de acervo e atividades.

    Args:
        user_data: dict ou objeto ORM com dados do usuário.
        firearms_data: lista de dicts com dados das armas (opcional).
        sessions_data: lista de dicts com dados das sessões (opcional).
    """
    buffer = BytesIO()
    user_name = _safe(_get(user_data, "name", "N/A"))
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"Relatório {user_name}")
    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='NormalCentered', parent=styles['Normal'], alignment=TA_CENTER))

    # Header
    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    if os.path.exists(logo_path):
        im = Image(logo_path, width=50, height=50)
        im.hAlign = 'LEFT'
        elements.append(im)

    title = Paragraph("<b>BALLISTIC PRO - RELATÓRIO DE ACERVO E ATIVIDADES</b>", styles['Title'])
    elements.append(title)
    elements.append(Paragraph(f"Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Section 1: User Info
    cr = _safe(_get(user_data, "cr_number") or "Não informado")
    addr = _safe(_get(user_data, "address_acervo") or "Não informado")
    cr_exp = _get(user_data, "cr_expiration")
    cr_exp_str = cr_exp.strftime('%d/%m/%Y') if cr_exp else 'N/A'

    data_user = [
        ["Nome Completo:", user_name],
        ["CPF:", _safe(_get(user_data, "cpf", "N/A"))],
        ["CR (Exército):", f"{cr} (Validade: {cr_exp_str})"],
        ["Endereço do Acervo:", Paragraph(addr, styles['Normal'])]
    ]
    elements.append(Paragraph("<b>1. DADOS DO ATIRADOR / CAC</b>", styles['Heading4']))
    t_user = Table(data_user, colWidths=[120, 350])
    t_user.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold')
    ]))
    elements.append(t_user)
    elements.append(Spacer(1, 18))

    # Section 2: Arsenal
    elements.append(Paragraph("<b>2. ACERVO DE ARMAS</b>", styles['Heading4']))
    firearms = firearms_data or []
    if firearms:
        data_guns = [["Tipo/Modelo", "Nº Série", "SIGMA", "CRAF"]]
        for f in firearms:
            data_guns.append([
                _get(f, "model", "-"),
                _get(f, "serial", "-"),
                _get(f, "sigma", "-"),
                _get(f, "craf", "-")
            ])
        t_guns = Table(data_guns, colWidths=[150, 100, 100, 100])
        t_guns.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t_guns)
    else:
        elements.append(Paragraph("Nenhuma arma cadastrada.", styles['Normal']))

    elements.append(Spacer(1, 18))

    # Section 3: Activities
    elements.append(Paragraph("<b>3. ÚLTIMAS ATIVIDADES</b>", styles['Heading4']))
    sessions = sessions_data or []
    if sessions:
        data_log = [["Data", "Calibre", "Carga", "Qtd"]]
        # Sort by date descending, take last 10
        sorted_sessions = sorted(sessions, key=lambda x: x.get("date", ""), reverse=True)[:10]
        for s in sorted_sessions:
            data_log.append([
                _get(s, "date_str", "N/A"),
                _get(s, "caliber", "N/A"),
                f"{_get(s, 'charge', 0)} gr",
                f"{_get(s, 'quantity', 0)} un"
            ])
        t_log = Table(data_log, colWidths=[100, 100, 100, 100])
        t_log.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t_log)
    else:
        elements.append(Paragraph("Nenhuma sessão registrada.", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def create_performance_report_v2(user, cv_results, analysis_img_bgr):
    """
    Generates a detailed Performance Report including the analyzed target image.
    Accepts user as dict or ORM object.
    """
    buffer = BytesIO()
    user_name = _safe(_get(user, "name", "N/A"))
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"Relatório Performance - {user_name}")
    elements = []
    styles = getSampleStyleSheet()

    # 1. Header
    title = Paragraph("<b>RELATÓRIO TÉCNICO DE BALÍSTICA E PRECISÃO</b>", styles['Title'])
    elements.append(title)
    elements.append(Paragraph(f"Atirador: {_safe(user_name)} | Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # 2. Analyzed Target Image
    elements.append(Paragraph("<b>1. ANÁLISE VISUAL DO ALVO</b>", styles['Heading4']))

    # UX-004: Usar buffer em memória (evita race condition em multi-usuário)
    is_success, img_buf = cv2.imencode('.jpg', cv_results['annotated_image'])
    if is_success:
        img_io = io.BytesIO(img_buf.tobytes())
        im = Image(img_io, width=450, height=350)
        im.hAlign = 'CENTER'
        elements.append(im)
    elements.append(Spacer(1, 12))

    # 3. Metrics Table
    elements.append(Paragraph("<b>2. MÉTRICAS DE AGRUPAMENTO (CV 2.0)</b>", styles['Heading4']))

    header = ["Grupo", "Impactos", "Agrupamento (mm)", "Desvio POI (X, Y)"]
    data = [header]

    for g in cv_results['groups']:
        px, py = g['poi_mm']
        data.append([
            f"G{g['id']}",
            len(g['shots']),
            f"{g['group_size_mm']:.2f} mm",
            f"{px:+.1f}, {py:+.1f} mm"
        ])

    t = Table(data, colWidths=[100, 100, 120, 130])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))

    # 4. Ballistic Conclusion
    elements.append(Paragraph("<b>3. PARECER TÉCNICO</b>", styles['Heading4']))
    total_shots = cv_results['shot_count']
    best_group = min([g['group_size_mm'] for g in cv_results['groups']]) if cv_results['groups'] else 0

    conclusion = f"""
    Foram detectados um total de {total_shots} impactos. 
    O melhor agrupamento registrado foi de {best_group:.2f} mm. 
    A análise indica uma dispersão {'CONSISTENTE' if best_group < 50 else 'ELEVADA'} para a distância informada.
    """
    elements.append(Paragraph(conclusion, styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
