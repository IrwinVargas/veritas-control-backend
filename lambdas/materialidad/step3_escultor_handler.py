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
from reportlab.platypus import Image

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

class CanvasPapelMembretadoVeritas(canvas.Canvas):
    """
    Clona milimétricamente el diseño geométrico de la imagen adjunta.
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
        
        # 🎨 PALETA DE COLORES EDITORIAL DE LA IMAGEN ADJUNTA
        c_bronce = colors.HexColor("#a18262")   # Tono café/bronce elegante
        c_arena = colors.HexColor("#d4c5b3")    # Tono arena claro de transición
        c_azul_oscuro = colors.HexColor("#1e293b") # Azul corporativo profundo de base
        
        # =========================================================================
        # 📐 GEOMETRÍA DEL ENCABEZADO (Top Header Trapecios)
        # =========================================================================
        # Trapecio Superior Derecho (Color Bronce de tu imagen)
        p_top = self.beginPath()
        p_top.moveTo(420, 792)
        p_top.lineTo(612, 792)
        p_top.lineTo(612, 720)
        p_top.lineTo(500, 720)
        self.setFillColor(c_bronce)
        self.drawPath(p_top, fill=True, stroke=False)

        # Listón Azul Oscuro Superior Esquinero
        p_top_azul = self.beginPath()
        p_top_azul.moveTo(560, 792)
        p_top_azul.lineTo(612, 792)
        p_top_azul.lineTo(612, 760)
        self.setFillColor(c_azul_oscuro)
        self.drawPath(p_top_azul, fill=True, stroke=False)
        
        # Línea de acentuación horizontal elegante debajo del bloque de logotipo
        self.setStrokeColor(c_arena)
        self.setLineWidth(1)
        self.line(45, 700, 567, 700)

        # =========================================================================
        # 📐 GEOMETRÍA DEL PIE DE PÁGINA (Bottom Footer Blocks de la Imagen)
        # =========================================================================
        # Bloque Base Azul Oscuro Inferior Completo
        self.setFillColor(c_azul_oscuro)
        self.rect(0, 0, 612, 35, fill=True, stroke=False)

        # Polígono Cruzado Izquierdo (Color Bronce)
        p_bot_bronce = self.beginPath()
        p_bot_bronce.moveTo(0, 0)
        p_bot_bronce.lineTo(140, 0)
        p_bot_bronce.lineTo(90, 65)
        p_bot_bronce.lineTo(0, 35)
        self.setFillColor(c_bronce)
        self.drawPath(p_bot_bronce, fill=True, stroke=False)

        # Polígono de Transición Arena
        p_bot_arena = self.beginPath()
        p_bot_arena.moveTo(90, 0)
        p_bot_arena.lineTo(190, 0)
        p_bot_arena.lineTo(150, 45)
        p_bot_arena.lineTo(120, 20)
        self.setFillColor(c_arena)
        self.drawPath(p_bot_arena, fill=True, stroke=False)

        # =========================================================================
        # 📝 TEXTOS METADATOS INMUTABLES (Footer Legal)
        # =========================================================================
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
    nombre_cliente = event.get('nombre_cliente')
    ano_fiscal = event.get('ano_fiscal', '2026')
    contrato = event.get('contrato', 'PRESTACION_SERVICIOS')
    texto_ia_crudo = event.get('texto_pericial', '')
    catalogo_json = event.get('catalogo_json_payload', [])

    bucket_name = os.environ.get('BUCKET_NAME')
    table_name = os.environ.get('DYNAMODB_TABLE')
    
    # Compilación binaria en memoria RAM del contenedor
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer, pagesize=letter,
        rightMargin=45, leftMargin=45, topMargin=110, bottomMargin=75
    )
    
    story = []
    
    # ... (Aquí continúa la inserción de párrafos, tablas y cláusulas del SAT) ...
    
    # 🎯 CONSTRUCCIÓN FINAL VINCULADA A TU CANVAS MAESTRO:
    # SAM invocará este CanvaMaker vectorizado con los trapecios bronce y azul marino
    doc.build(story, canvasmaker=CanvasPapelMembretadoVeritas)
    print("🎨 Estructura geométrica del PDF renderizada en la RAM del contenedor.")

    # =========================================================================
    # 🚀 LA REPARACIÓN REINA: REBOBINAMOS EL CURSOR AL PUNTO CERO (ORIGEN)
    # Sin esta línea, boto3 lee un string vacío y S3 se queda en blanco de por vida.
    # =========================================================================
    pdf_buffer.seek(0)
    
    # Extraemos los bytes puros ya rebobinados desde el inicio
    pdf_bytes_reales = pdf_buffer.getvalue()
    print(f"📦 Tamaño real del PDF pericial a inyectar: {len(pdf_bytes_reales)} bytes.")

    # Nombre dinámico inmutable para tu búnker de S3 multi-tenant
    s3_key_pdf = f"{tenant_id}/{rfc_cliente}/{ano_fiscal}/{contrato}/Contrato_Prestacion_Servicios_Firmado.pdf"

    print(f"💾 Transmitiendo PDF definitivo de forma interna hacia S3: {bucket_name}/{s3_key_pdf}")
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key_pdf,
        Body=pdf_bytes_reales, # 🎯 Entran los bytes reales de forma simétrica
        ContentType='application/pdf'
    )
    
    # Liberamos la memoria de la RAM para mantener el performance en microsegundos limpios
    pdf_buffer.close()

    print("🎯 ¡Búnker de materialidad consolidado con éxito físico real en Amazon S3!")
    return {"status": "FINISHED", "s3_key": s3_key_pdf}