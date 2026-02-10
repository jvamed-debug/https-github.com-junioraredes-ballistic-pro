from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
from datetime import datetime
import cv2
import os

def create_inspection_report(user):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"Relatório {user.name}")
    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='NormalCentered', parent=styles['Normal'], alignment=TA_CENTER))
    
    # Header
    if os.path.exists("logo.png"):
        im = Image("logo.png", width=50, height=50)
        im.hAlign = 'LEFT'
        elements.append(im)
        
    title = Paragraph("<b>BALLISTIC PRO - RELATÓRIO DE ACERVO E ATIVIDADES</b>", styles['Title'])
    elements.append(title)
    elements.append(Paragraph(f"Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # ... (Keep existing User Info and Arsenal sections) ...
    # Section 1: User Info
    cr = user.cr_number if user.cr_number else "Não informado"
    addr = user.address_acervo if user.address_acervo else "Não informado"
    data_user = [["Nome Completo:", user.name], ["CPF:", user.cpf], ["CR (Exército):", f"{cr} (Validade: {user.cr_expiration.strftime('%d/%m/%Y') if user.cr_expiration else 'N/A'})"], ["Endereço do Acervo:", Paragraph(addr, styles['Normal'])]]
    elements.append(Paragraph("<b>1. DADOS DO ATIRADOR / CAC</b>", styles['Heading4']))
    t_user = Table(data_user, colWidths=[120, 350])
    t_user.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold')]))
    elements.append(t_user)
    elements.append(Spacer(1, 18))

    # Section 2: Arsenal
    elements.append(Paragraph("<b>2. ACERVO DE ARMAS</b>", styles['Heading4']))
    if user.firearms:
        data_guns = [["Tipo/Modelo", "Nº Série", "SIGMA", "CRAF"]]
        for f in user.firearms: data_guns.append([f.model, f.serial or "-", f.sigma or "-", f.craf or "-"] )
        t_guns = Table(data_guns, colWidths=[150, 100, 100, 100])
        t_guns.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.darkblue), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 1, colors.black)]))
        elements.append(t_guns)
    
    elements.append(Spacer(1, 18))

    # Section 3: Activities
    elements.append(Paragraph("<b>3. ÚLTIMAS ATIVIDADES</b>", styles['Heading4']))
    if user.sessions:
        data_log = [["Data", "Calibre", "Carga", "Qtd"]]
        for s in sorted(user.sessions, key=lambda x: x.date, reverse=True)[:10]:
            data_log.append([s.date.strftime('%d/%m/%Y'), s.caliber, f"{s.charge} gr", f"{s.quantity} un"])
        t_log = Table(data_log, colWidths=[100, 100, 100, 100])
        t_log.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.darkred), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 1, colors.black)]))
        elements.append(t_log)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def create_performance_report_v2(user, cv_results, analysis_img_bgr):
    """
    Generates a detailed Performance Report including the analyzed target image.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"Relatório Performance - {user.name}")
    elements = []
    styles = getSampleStyleSheet()
    
    # 1. Header
    title = Paragraph(f"<b>RELATÓRIO TÉCNICO DE BALÍSTICA E PRECISÃO</b>", styles['Title'])
    elements.append(title)
    elements.append(Paragraph(f"Atirador: {user.name} | Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # 2. Analyzed Target Image
    elements.append(Paragraph("<b>1. ANÁLISE VISUAL DO ALVO</b>", styles['Heading4']))
    
    # Save CV image temporarily for PDF
    temp_img_path = f"temp_analysis_{user.id}.jpg"
    cv2.imwrite(temp_img_path, cv_results['annotated_image'])
    
    im = Image(temp_img_path, width=450, height=350)
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
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
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
    
    # Cleanup
    if os.path.exists(temp_img_path): os.remove(temp_img_path)
    
    buffer.seek(0)
    return buffer.getvalue()
