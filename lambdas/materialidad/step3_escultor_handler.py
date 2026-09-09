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
        
        # 🎨 PALETA DE COLORES EDITORIAL DE LA MUESTRA VISUAL
        c_bronce = colors.HexColor("#a18262")   
        c_arena = colors.HexColor("#d4c5b3")    
        c_azul_oscuro = colors.HexColor("#1e293b") 
        
        # 📐 GEOMETRÍA DEL ENCABEZADO (Top Header Trapecios)
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

        # 📐 GEOMETRÍA DEL PIE DE PÁGINA (Bottom Footer Blocks)
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

        # 📝 TEXTOS METADATOS INMUTABLES JURÍDICOS (Footer Legal)
        self.setFont("Helvetica-Bold", 7)
        self.setFillColor(colors.white)
        self.drawString(160, 14, "CONMUTADOR: +52 55 6730 4204")
        self.drawCentredString(340, 14, "ENLACE: CONTACTO@BUFETEVERITAS.COM")
        self.drawRightString(567, 14, f"AUDITORÍA ART. 69-B CFF — PÁG {self._pageNumber} DE {total_paginas}")
        
        self.restoreState()


def handler(event, context):
    print("🎨 Paso 3 Activo: Inicializando maquetación robusta y editorial premium...")
    
    tenant_id = event.get('tenant_id')
    rfc_cliente = event.get('rfc_cliente')
    nombre_cliente = event.get('nombre_cliente', 'CONTRIBUYENTE AUDITADO')
    ano_fiscal = event.get('ano_fiscal', '2026')
    contrato = event.get('contrato', 'PRESTACION_SERVICIOS')
    
    # Succionamos el texto legal pericial que Claude 4.5 redactó en el Paso 2
    texto_ia_crudo = event.get('texto_pericial', '')
    if not texto_ia_crudo:
        texto_ia_crudo = "<b>CONTRATO MAESTRO JURÍDICO.</b> Se certifica la materialidad de operaciones mutuas."

    bucket_name = os.environ.get('BUCKET_NAME')
    
    # Inicializamos buffer binario en la RAM del contenedor
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer, pagesize=letter,
        rightMargin=45, leftMargin=45, topMargin=110, bottomMargin=75
    )
    
    story = []
    
    # 🎨 CARGA Y CONFIGURACIÓN DE ESTILOS EDITORIALES RÍGIDOS
    styles = getSampleStyleSheet()
    
    style_titulo = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1e293b"),
        alignment=TA_LEFT,
        spaceAfter=15
    )
    
    style_sub = ParagraphStyle(
        'DocSub',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#a18262"),
        alignment=TA_LEFT,
        spaceAfter=30
    )
    
    style_legal_body = ParagraphStyle(
        'DocLegalBody',
        fontName='Helvetica',
        fontSize=10,
        leading=16,
        textColor=colors.HexColor("#334155"),
        alignment=TA_JUSTIFY,
        spaceAfter=12
    )

    # 🚀 REPARACIÓN REINA 1: Sembramos elementos reales dentro de la lista 'story'
    # para que doc.build() se ejecute con éxito y no se quede en blanco
    story.append(Paragraph("EXPEDIENTE FORENSE DE EXCLUSIÓN TRIBUTARIA", style_titulo))
    story.append(Paragraph(f"CLIENTE: {nombre_cliente} | RFC: {rfc_cliente} | EJERCICIO: {ano_fiscal}", style_sub))
    story.append(Spacer(1, 15))
    
    # Rompemos el string de la IA en párrafos limpios por saltos de línea e inyectamos
    for fragmento in texto_ia_crudo.split('\n'):
        if fragmento.strip():
            story.append(Paragraph(fragmento.strip(), style_legal_body))
            
    story.append(Spacer(1, 20))
    
    # 🎯 CONSTRUCCIÓN VINCULADA A TU CANVAS GEOMÉTRICO:
    doc.build(story, canvasmaker=CanvasPapelMembretadoVeritas)
    print("🎨 Estructura geométrica del PDF renderizada en la RAM del contenedor.")

    # 🚀 REPARACIÓN REINA 2: Rebobinamos el cursor al punto cero (origen) de la RAM
    pdf_buffer.seek(0)
    pdf_bytes_reales = pdf_buffer.getvalue()
    
    print(f"📦 Tamaño real del PDF pericial a inyectar: {len(pdf_bytes_reales)} bytes.")

    # Nombre dinámico inmutable para tu búnker de S3 multi-tenant
    s3_key_pdf = f"{tenant_id}/{rfc_cliente}/{ano_fiscal}/{contrato}/Contrato_Prestacion_Servicios_Firmado.pdf"

    print(f"💾 Transmitiendo PDF definitivo de forma interna hacia S3: {bucket_name}/{s3_key_pdf}")
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key_pdf,
        Body=pdf_bytes_reales, # Entran los bytes reales de forma simétrica
        ContentType='application/pdf'
    )
    
    pdf_buffer.close()
    print("🎯 ¡Búnker de materialidad consolidado con éxito físico real en Amazon S3!")
    
    return {"status": "FINISHED", "s3_key": s3_key_pdf}
