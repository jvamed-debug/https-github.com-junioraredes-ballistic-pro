from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
from datetime import datetime
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
    
    # 1. User Info
    elements.append(Paragraph("<b>1. DADOS DO ATIRADOR / CAC</b>", styles['Heading4']))
    
    # Safe check for None values
    cr = user.cr_number if user.cr_number else "Não informado"
    addr = user.address_acervo if user.address_acervo else "Não informado"
    
    data_user = [
        ["Nome Completo:", user.name],
        ["CPF:", user.cpf],
        ["CR (Exército):", f"{cr} (Validade: {user.cr_expiration.strftime('%d/%m/%Y') if user.cr_expiration else 'N/A'})"],
        ["Endereço do Acervo:", Paragraph(addr, styles['Normal'])]
    ]
    t_user = Table(data_user, colWidths=[120, 350])
    t_user.setStyle(TableStyle([
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_user)
    elements.append(Spacer(1, 18))

    # 2. Arsenal (Acervo)
    elements.append(Paragraph("<b>2. ACERVO DE ARMAS CADASTRADO</b>", styles['Heading4']))
    if user.firearms:
        # Header Row
        data_guns = [["Tipo/Modelo", "Nº Série", "SIGMA", "CRAF", "Validade"]]
        for f in user.firearms:
            exp_date = f.expiration.strftime('%d/%m/%Y') if f.expiration else '-'
            data_guns.append([
                f.model, 
                f.serial or "-", 
                f.sigma or "-", 
                f.craf or "-", 
                exp_date
            ])
        
        t_guns = Table(data_guns, colWidths=[150, 80, 80, 80, 80])
        t_guns.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.white])
        ]))
        elements.append(t_guns)
    else:
        elements.append(Paragraph("<i>Nenhuma arma cadastrada neste perfil.</i>", styles['Normal']))
    
    elements.append(Spacer(1, 18))

    # 3. Reload Log (Logbook)
    elements.append(Paragraph("<b>3. REGISTRO DE RECARGAS (Últimas 30 Atividades)</b>", styles['Heading4']))
    if user.sessions:
        data_log = [["Data", "Calibre", "Componentes (Projétil | Pólvora)", "Carga", "Qtd"]]
        
        # Sort chronologically desc
        sessions = sorted(user.sessions, key=lambda x: x.date, reverse=True)[:30]
        
        for s in sessions:
            components = f"{s.projectile}\n{s.powder}"
            data_log.append([
                s.date.strftime('%d/%m/%Y'),
                s.caliber,
                components,
                f"{s.charge} gr",
                f"{s.quantity} un"
            ])
            
        t_log = Table(data_log, colWidths=[60, 100, 200, 60, 50])
        t_log.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkred),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.white])
        ]))
        elements.append(t_log)
    else:
        elements.append(Paragraph("<i>Nenhuma atividade de recarga registrada.</i>", styles['Normal']))

    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("_" * 50, styles['NormalCentered']))
    elements.append(Paragraph(f"<b>{user.name}</b>", styles['NormalCentered']))
    elements.append(Paragraph("Responsável pelo Acervo", styles['NormalCentered']))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
