import os
import json
import io
import boto3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib import colors

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

class CanvasPapelMembretadoVeritas(canvas.Canvas):
    """
    Clona milimétricamente el diseño geométrico de la imagen corporativa.
    Dibuja polígonos vectoriales en los extremos de la hoja sin invadir el margen de texto.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_decoraciones_veritas(page_count)
            super().showPage()
        super().save()

    def draw_decoraciones_veritas(self, total_paginas):
        self.saveState()
        
        c_bronce = colors.HexColor("#a18262")   
        c_arena = colors.HexColor("#d4c5b3")    
        c_azul_oscuro = colors.HexColor("#1e293b") 
        
        p_top = self.beginPath()
        p_top.moveTo(420, 792)
        p_top.lineTo(612, 792)
        p_top.lineTo(612, 720)
        p_top.lineTo(500, 720)
        self.setFillColor(c_bronce)
        self.drawPath(p_top, fill=True, stroke=False)

        p_top_azul = self.beginPath()
        p_top_azul.moveTo(560, 792)
        p_top_azul.lineTo(612, 792)
        p_top_azul.lineTo(612, 760)
        self.setFillColor(c_azul_oscuro)
        self.drawPath(p_top_azul, fill=True, stroke=False)
        
        self.setStrokeColor(c_arena)
        self.setLineWidth(1)
        self.line(45, 700, 567, 700)

        self.setFillColor(c_azul_oscuro)
        self.rect(0, 0, 612, 35, fill=True, stroke=False)

        p_bot_bronce = self.beginPath()
        p_bot_bronce.moveTo(0, 0)
        p_bot_bronce.lineTo(140, 0)
        p_bot_bronce.lineTo(90, 65)
        p_bot_bronce.lineTo(0, 35)
        self.setFillColor(c_bronce)
        self.drawPath(p_bot_bronce, fill=True, stroke=False)

        p_bot_arena = self.beginPath()
        p_bot_arena.moveTo(90, 0)
        p_bot_arena.lineTo(190, 0)
        p_bot_arena.lineTo(150, 45)
        p_bot_arena.lineTo(120, 20)
        self.setFillColor(c_arena)
        self.drawPath(p_bot_arena, fill=True, stroke=False)

        self.setFont("Helvetica-Bold", 7)
        self.setFillColor(colors.white)
        self.drawString(160, 14, "CONMUTADOR: +52 55 6730 4204")
        self.drawCentredString(340, 14, "ENLACE: CONTACTO@BUFETEVERITAS.COM")
        self.drawRightString(567, 14, f"AUDITORÍA ART. 69-B CFF — PÁG {self._pageNumber} DE {total_paginas}")
        
        self.restoreState()


def handler(event, context):
    print("🎨 Paso 3 Activo: Ejecutando maquetación robusta y editorial premium...")
    
    tenant_id = event.get('tenant_id', 'bufete-veritas-uuid-1111')
    rfc_cliente = event.get('rfc_cliente', 'AAA080808HL8')
    nombre_cliente = event.get('nombre_cliente', 'REAL CLEAN DISTRIBUCIONES S.A. DE C.V.')
    ano_fiscal = event.get('ano_fiscal', '2026')
    contrato = event.get('contrato', 'DESARROLLO_TECNOLOGICO')
    
    # Succionamos los payloads asíncronos de la Step Function
    texto_ia_crudo = event.get('texto_pericial', '')
    if not texto_ia_crudo and 'step2_output' in event:
        texto_ia_crudo = event.get('step2_output', {}).get('texto_pericial', '')

    conceptos_sat_crudos = event.get('string_catalogo_ia', '')
    if not conceptos_sat_crudos and 'step1_output' in event:
        conceptos_sat_crudos = event.get('step1_output', {}).get('string_catalogo_ia', '')

    bucket_name = os.environ.get('BUCKET_NAME') or "veritas-control-materialidad-dev"
    
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer, pagesize=letter,
        rightMargin=45, leftMargin=45, topMargin=110, bottomMargin=75
    )
    
    story = []
    
    # Configuración de tus hojas de estilo ejecutivas premium (Look de tu imagen)
    styles = getSampleStyleSheet()
    
    style_titulo = ParagraphStyle(
        'DocTitle', fontName='Helvetica-Bold', fontSize=16, leading=20,
        textColor=colors.HexColor("#1e293b"), alignment=TA_LEFT, spaceAfter=8
    )
    style_sub = ParagraphStyle(
        'DocSub', fontName='Helvetica-Bold', fontSize=9, leading=12,
        textColor=colors.HexColor("#a18262"), alignment=TA_LEFT, spaceAfter=25
    )
    style_legal_body = ParagraphStyle(
        'DocLegalBody', fontName='Helvetica', fontSize=9.5, leading=16,
        textColor=colors.HexColor("#334155"), alignment=TA_JUSTIFY, spaceAfter=14
    )

    # Llenado denso del array story para activar el motor ReportLab
    story.append(Paragraph("EXPEDIENTE FORENSE DE INMUTABILIDAD Y EXCLUSIÓN TRIBUTARIA", style_titulo))
    story.append(Paragraph(f"CLIENTE: {nombre_cliente} | RFC: {rfc_cliente} | EJERCICIO FISCAL: {ano_fiscal}", style_sub))
    story.append(Spacer(1, 10))
    
    # Desglosamos e inyectamos los párrafos robustos
    texto_ia_limpio = texto_ia_crudo.replace("```html", "").replace("```", "").strip()
    
    # Desglosamos e inyectamos los párrafos robustos purificados
    for fragmento in texto_ia_limpio.split('\n'):
        if fragmento.strip():
            story.append(Paragraph(fragmento.strip(), style_legal_body))
            
    story.append(Spacer(1, 30))
            
    style_firma_linea = ParagraphStyle(
        'FirmaLinea', fontName='Helvetica', fontSize=9, leading=12, alignment=TA_CENTER
    )
    
    col_izquierda = [
        Spacer(1, 40),
        Paragraph("________________________________________", style_firma_linea),
        Spacer(1, 4),
        Paragraph("<b>REPRESENTANTE LEGAL ASIGNADO</b>", style_firma_linea),
        Paragraph(f"{nombre_cliente}", style_firma_linea)
    ]
    
    col_derecha = [
        Spacer(1, 40),
        Paragraph("________________________________________", style_firma_linea),
        Spacer(1, 4),
        Paragraph("<b>PERITO FISCAL RESPONSABLE</b>", style_firma_linea),
        Paragraph("BUFETE JURÍDICO VERITAS CONTROL", style_firma_linea)
    ]
    
    # Encapsulamos las firmas en una tabla y usamos KeepTogether para que nunca se corten solas
    tabla_firmas = Table([[col_izquierda, col_derecha]], colWidths=[260, 260])
    tabla_firmas.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    
    # Forzamos que el bloque de firmas viaje compacto y no se rompa a la mitad
    story.append(KeepTogether(tabla_firmas))
    
    # 🎯 CONSTRUCCIÓN FINAL VINCULADA A TU CANVAS GEOMÉTRICO:
    doc.build(story, canvasmaker=CanvasPapelMembretadoVeritas)
    print("🎨 Estructura purificada y firmada renderizada en S3.")
    
    # Rebobinado binario milimétrico anti-0 bytes
    pdf_buffer.seek(0)
    pdf_bytes_reales = pdf_buffer.getvalue()

    s3_key_pdf = f"{tenant_id}/{rfc_cliente}/{ano_fiscal}/{contrato}/Contrato_Prestacion_Servicios_Firmado.pdf"
    
    s3_client.put_object(
        Bucket=str(bucket_name).strip(),
        Key=s3_key_pdf,
        Body=pdf_bytes_reales,
        ContentType='application/pdf'
    )
    pdf_buffer.close()
    
    print("🎯 ¡Búnker de materialidad consolidado con densidad de texto real en Amazon S3!")
    return {"status": "FINISHED", "s3_key": s3_key_pdf}
