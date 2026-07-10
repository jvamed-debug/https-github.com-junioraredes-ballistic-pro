from reportlab.lib import colors
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from io import BytesIO

def create_label_pdf(session, user_name):
    """
    Generates a PDF label for ammo box.
    Dimensions: 100mm x 60mm (Standard large label)
    """
    width, height = 100 * mm, 60 * mm
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(width, height))
    
    # Border
    c.setLineWidth(1)
    c.setStrokeColor(colors.black)
    c.rect(2*mm, 2*mm, width-4*mm, height-4*mm)
    
    # Header
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, height - 10*mm, "BALLISTIC PRO - DADOS DE RECARGA")
    
    # Content
    c.setFont("Helvetica", 10)
    line_height = 5 * mm
    start_y = height - 18 * mm
    x_pos = 6 * mm
    
    # Left Column
    c.drawString(x_pos, start_y, f"Data: {session.date.strftime('%d/%m/%Y')}")
    c.drawString(x_pos, start_y - line_height, f"Calibre: {session.caliber}")
    c.drawString(x_pos, start_y - 2*line_height, f"Projétil: {session.projectile}")
    c.drawString(x_pos, start_y - 3*line_height, f"Pólvora: {session.powder}")
    c.drawString(x_pos, start_y - 4*line_height, f"Carga: {session.charge} gr")
    
    # Right Column (Offset)
    x_pos_right = 55 * mm
    c.drawString(x_pos_right, start_y, f"Qtd: {session.quantity}")
    c.drawString(x_pos_right, start_y - line_height, f"Espoleta: {session.primer or 'N/A'}")
    c.drawString(x_pos_right, start_y - 2*line_height, f"Estojo: {session.case or 'N/A'}")
    if session.velocity_avg:
        c.drawString(x_pos_right, start_y - 3*line_height, f"Vel: {session.velocity_avg} fps")
    
    # Footer Note
    c.setFont("Helvetica-Oblique", 8)
    note = session.notes[:50] + "..." if session.notes and len(session.notes) > 50 else (session.notes or "")
    c.drawString(x_pos, 8*mm, f"Obs: {note}")
    
    # Operator
    c.setFont("Helvetica", 6)
    c.drawRightString(width - 4*mm, 4*mm, f"Op: {user_name}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
