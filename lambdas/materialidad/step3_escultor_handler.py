import os
import json
import io
import boto3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import Image

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

class CanvasForenseSate(canvas.Canvas):
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
            if self._pageNumber > 1:
                self.saveState()
                self.setFillColor("#b91c1c")
                self.rect(0, 0, 12, 792, fill=True, stroke=False)
                self.rect(600, 0, 12, 792, fill=True, stroke=False)
                self.setFont("Helvetica-Bold", 7)
                self.setFillColor("#1e293b")
                self.line(36, 45, 576, 45)
                self.drawString(36, 32, "VERITAS SUITE - EXPEDIENTE FORENSE DIGITAL COMPLIANCE")
                self.drawRightString(576, 32, f"Página {self._pageNumber} de {page_count}")
                self.restoreState()
            super().showPage()
        super().save()

def handler(event, context):
    print("🎨 Paso 3 Activo: Modelado gráfico en ReportLab y sellado inmutable en S3...")
    
    tenant_id = event.get('tenant_id')
    rfc_cliente = event.get('rfc_cliente')
    nombre_cliente = event.get('nombre_cliente')
    ano_fiscal = event.get('ano_fiscal')
    contrato = event.get('contrato')
    texto_pericial = event.get('texto_pericial')
    catalogo_json = event.get('catalogo_json_payload', [])

    bucket_name = os.environ.get('BUCKET_NAME')
    table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE'))

    # Actualizamos barra de progreso a 75%
    hash_key = f"{tenant_id}#{rfc_cliente}#{contrato}#{ano_fiscal}"
    table.update_item(
        Key={'tenant_rfc_year_contract': hash_key},
        UpdateExpression="SET progreso_porcentaje = :p, mensaje_progreso = :m",
        ExpressionAttributeValues={
            ':p': 75, 
            ':m': "ReportLab compilando portada formal, cintillos vino y tabla de precios cebra..."
        }
    )
    

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    style_h1 = ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=13, leading=16, textColor='#0f172a', spaceBefore=14, spaceAfter=8)
    style_body = ParagraphStyle('BL', fontName='Helvetica', fontSize=10, leading=15, textColor='#334155', alignment=TA_JUSTIFY, spaceAfter=8)
    style_th = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor='#ffffff', alignment=TA_CENTER)
    style_td = ParagraphStyle('TD', fontName='Helvetica', fontSize=9, leading=11, textColor='#1e293b')

    story = [Paragraph(f"LIBRO CORPORATIVO DE MATERIALIDAD EVOLUTIVA — EJERCICIO {ano_fiscal}", style_h1), Spacer(1, 15)]
    
    # 🚀 RENDERIZACIÓN PURA LIBRE DE ALMOHADILLAS #
    for line in texto_pericial.split('\n'):
        if line.strip(): story.append(Paragraph(line.strip().replace('#', '').replace('*', ''), style_body))

    # Construcción de la Tabla Cebra con descarga asíncrona de imágenes
    t_data = [[Paragraph("Evidencia Fotográfica", style_th), Paragraph("Concepto de Referencia", style_th), Paragraph("Valor Comercial", style_th)]]
    
    for prod in catalogo_json:
        img_obj = None
        key_foto = prod.get('key_foto', '')
        if key_foto:
            try:
                obj_f = s3_client.get_object(Bucket=bucket_name, Key=key_foto)
                img_obj = Image(io.BytesIO(obj_f['body'].read()), width=35, height=30)
            except Exception: pass
            
        t_data.append([img_obj if img_obj else "—", Paragraph(prod['desc'], style_td), Paragraph(f"$ {prod['precio']:,.2f} MXN", style_td)])

    tabla_r = Table(t_data, colWidths=)
    tabla_r.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(Spacer(1, 15))
    story.append(tabla_r)

    doc.build(story, canvasmaker=CanvasForenseSate)
    pdf_buffer.seek(0)
    pdf_bytes = pdf_buffer.read()

    # Ruta de destino inmutable cronológica en S3
    s3_key_final = f"{tenant_id}/{rfc_cliente}/{ano_fiscal}/{contrato}/02 Materialidad/01 Libro_Forense_Consolidado.pdf"
    s3_client.put_object(Bucket=bucket_name, Key=s3_key_final, Body=pdf_bytes, ContentType='application/pdf')

    url_firmada = s3_client.generate_presigned_url(ClientMethod='get_object', Params={'Bucket': bucket_name, 'Key': s3_key_final}, ExpiresIn=1800)

    # 📊 SELLO FINAL 100% COMPLETO EN DYNAMODB NOSQL
    table.update_item(
        Key={'tenant_rfc_year_contract': hash_key},
        UpdateExpression="SET progreso_porcentaje = :p, mensaje_progreso = :m, estatus_global = :e, archivos.materialidad = :m_file",
        ExpressionAttributeValues={
            ':p': 100, 
            ':m': "¡Expediente Forense Completo y Sella con Éxito!",
            ':e': 'COMPLETO',
            ':m_file': {"status": "COMPLETO", "s3_key": s3_key_final, "download_url": url_firmada, "updated_at": datetime.utcnow().isoformat() + "Z"}
        }
    )
    print(f"🎯 Expediente sellado en S3 exitosamente: {s3_key_final}")
    return {"status": "SUCCEEDED"}
