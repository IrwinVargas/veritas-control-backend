import os
import io
import json
import boto3
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib import colors
from reportlab.pdfgen import canvas

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# =========================================================================
# 🎨 CANVAS MEMBRETADO JURÍDICO (DIBUJA EL DISEÑO EXACTO DE TU IMAGEN)
# =========================================================================
class CanvasMembretadoRouchers(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        # Ciclo de renderizado de dos pasadas para numeración exacta de hojas
        num_paginas = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.dibujar_elementos_marca(num_paginas)
            super().showPage()
        super().save()

    def dibujar_elementos_marca(self, total_paginas):
        self.saveState()
        
        # 🎨 CODIFICACIÓN DE COLORES DE LA IMAGEN ADJUNTA
        color_bronce = colors.HexColor("#a18262") # Tono bronce/oro viejo elegante
        color_negro_solido = colors.HexColor("#0f1115") # Negro institucional
        
        # 🏛️ 1. ENCABEZADO GEOMÉTRICO DIAGONAL SUPERIOR
        # Dibujamos el bloque negro superior derecho de tu imagen
        path_negro = self.beginPath()
        path_negro.moveTo(250, 792) # Punto de quiebre diagonal
        path_negro.lineTo(612, 792) # Esquina superior derecha
        path_negro.lineTo(612, 690) # Lateral derecho bajo
        path_negro.lineTo(340, 740) # Cierre diagonal
        path_negro.close()
        self.setFillColor(color_negro_solido)
        self.drawPath(path_negro, fill=1, stroke=0)
        
        # Dibujamos la franja bronce/oro viejo que abraza el encabezado izquierdo
        path_bronce = self.beginPath()
        path_bronce.moveTo(0, 792)  # Esquina superior izquierda
        path_bronce.lineTo(250, 792)
        path_bronce.lineTo(340, 740)
        path_bronce.lineTo(0, 740)   # Línea recta horizontal izquierda
        path_bronce.close()
        self.setFillColor(color_bronce)
        self.drawPath(path_bronce, fill=1, stroke=0)

        # Textos informativos de ROUCHERS adentro del bloque negro (Idéntico a tu imagen)
        self.setFillColor(colors.white)
        self.setFont("Helvetica-Bold", 8)
        self.drawRightString(580, 720, "Ph: +52 55 6730 4204  |  Fax: Forense Digital")
        self.drawRightString(580, 705, "Email: contacto@rouchers.com.mx")
        
        self.setFillColor(color_negro_solido)
        self.setFont("Helvetica-Bold", 14)
        self.drawString(45, 755, "ROUCHERS, S.C.")
        self.setFont("Helvetica", 8)
        self.drawString(45, 745, "Despacho de Peritos Fiscales de Élite")

        # 🏛️ 2. PIE DE PÁGINA CORPORATIVO BRONCE (BLOQUE RECTANGULAR DE TU IMAGEN)
        self.setFillColor(color_bronce)
        self.rect(0, 0, 612, 60, fill=1, stroke=0)
        
        # Datos de localización impresos en blanco limpio sobre el pie de página
        self.setFillColor(colors.white)
        self.setFont("Helvetica", 9)
        self.drawString(45, 34, "DOMICILIO FISCAL REAL: Paseo de la Reforma 405, Piso 12, Cuauhtémoc, CDMX, C.P. 06500")
        self.drawString(45, 20, "Ecosistema Automatizado Inmune a Exclusiones del Artículo 69-B del CFF")
        
        # Contador dinámico de hojas a la derecha
        self.drawRightString(567, 20, f"Página {self._pageNumber} de {total_paginas}")
        
        self.restoreState()

# =========================================================================
# ⚙️ PARSER MAESTRO: TRANSFORMA MARKDOWN EN ETIQUETAS LEPAN COMPATIBLES HTML
# =========================================================================
def parsear_markdown_a_html_reportlab(texto_markdown):
    if not texto_markdown:
        return ""
    
    # 🚀 REPARACIÓN REINA SÉNIOR DE PARSING:
    # Barremos los hashtags de Markdown que se le escapan a Bedrock antes de fracturar las líneas
    texto = str(texto_markdown).replace("\r", "")
    texto = texto.replace("# ", "").replace("## ", "").replace("### ", "")
    
    # Traducimos asteriscos dobles (**texto**) a negritas válidas HTML de ReportLab
    texto = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto)
    texto = re.sub(r'-\s+(.*?)\n', r'• \1<br/>', texto)
    
    return texto

def handler(event, context):
    print("🎨 Paso 3 Activo: Desplegando el Escultor Vectorial con la Plantilla de la Imagen...")
    
    tenant_id = event.get('tenant_id', 'bufete-veritas-uuid-1111')
    rfc_cliente = event.get('rfc_cliente', '')
    ano_fiscal = event.get('ano_fiscal', '2026')
    tenant_rfc = event.get('tenant_rfc', f"{tenant_id}#{rfc_cliente}")
    
    # Succionamos el array crudo que escupió tu Paso 2 corregido
    archivos_a_esculpir = event.get('archivos_redactados_ia')
    
    if not archivos_a_esculpir and 'step2_output' in event:
        archivos_a_esculpir = event.get('step2_output', {}).get('archivos_redactados_ia', [])

    if not archivos_a_esculpir:
        print("⚠️ Advertencia: Array de textos vacío. Saltando rendering.")
        return {"status": "SKIPPED", "reason": "No documents provided"}

    bucket_name = os.environ.get('BUCKET_NAME', 'veritas-control-materialidad-dev')
    nombre_tabla = os.environ.get('NOTIFICACIONES_TABLE', 'veritas-control-materialidad-nosql-dev')
    table = dynamodb.Table(nombre_tabla)

    for doc in archivos_a_esculpir:
        nombre_file = doc["nombre_archivo"]
        folder_sat = doc["folder_seccion"]
        markdown_ia = doc["prosa_completa_ia"]

        # 🚀 EJECUCIÓN DEL PARSER: Transformamos el Markdown hostil a HTML legal legible
        prosa_html_limpia = parsear_markdown_a_html_reportlab(markdown_ia)

        pdf_buffer = io.BytesIO()
        # Calzamos márgenes amplios para que el texto jamás choque con tus bloques geométricos superior e inferior
        doc_template = SimpleDocTemplate(
            pdf_buffer, pagesize=letter,
            rightMargin=45, leftMargin=45, topMargin=130, bottomMargin=90
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        style_legal_body = ParagraphStyle(
            'PlantillaImagenBody', fontName='Helvetica', fontSize=10, leading=16,
            textColor=colors.HexColor("#2d3748"), alignment=TA_JUSTIFY, spaceAfter=12
        )

        # Inyectamos el contenido limpio formateado
        for fragmento in prosa_html_limpia.split('<br/>'):
            if fragmento.strip():
                story.append(Paragraph(fragmento.strip(), style_legal_body))

        # Compilación acoplada usando el canvasmaker personalizado de la imagen
        doc_template.build(story, canvasmaker=CanvasMembretadoRouchers)
        pdf_bytes_reales = pdf_buffer.getvalue()

        # Coordenada exacta de almacenamiento segregada por tus 4 Phase SAT folders
        s3_key_pdf = f"{tenant_id}/{rfc_cliente}/{ano_fiscal}/{folder_sat}/{nombre_file}"
        
        print(f"📡 Sembrando PDF de alta gama en S3: [{s3_key_pdf}]")
        s3_client.put_object(
            Bucket=str(bucket_name).strip(),
            Key=s3_key_pdf,
            Body=pdf_bytes_reales,
            ContentType='application/pdf'
        )
        pdf_buffer.close()
        
        DICCIONARIO_LLAVES_NATIVAS_FRONT = {
            "CONTRATO_PRESTACION_SERVICIOS": "materialidad",
            "ACTA_CONSTITUTIVA_RESPALDO": "acta_constitutiva",
            "IDENTIFICACION_REPRESENTANTE_LEGAL": "identificacion_legal",
            "DICTAMEN_OPINION_32D": "opinion_32d",
            "CONSTANCIA_SITUACION_FISCAL_CEDULA": "constancia_fiscal",
            "BITACORA_CONTROL_ASISTENCIA": "reporte_actividades", # Sincronizado a tu entrega original
            "MEMORIA_FOTOGRAFICA_GEOLOCALIZADA": "evidencia_multimedia",
            "INFORME_FLUJO_BANCARIO": "estado_cuenta",
            "CONCILIACION_XML_COMPROBANTES": "zip_consolidado"
        }

        # Habilitamos la descarga en caliente parcial en React de este archivo individual
        llave_front_real = DICCIONARIO_LLAVES_NATIVAS_FRONT.get(doc["id_documento"], doc["id_documento"].lower())
        
        print(f"💾 Sincronizando en caliente: Escribiendo llave [{llave_front_real}] en DynamoDB para tu Front-End...")
        table.update_item(
            Key={'tenant_rfc': tenant_rfc},
            UpdateExpression=f"SET {llave_front_real} = :m, estatus_global = :s",
            ExpressionAttributeValues={
                ':m': {
                    'status': 'COMPLETO',
                    'download_url': f"https://{bucket_name}://{s3_key_pdf}",
                    'packaged_at': datetime.utcnow().isoformat()
                },
                ':s': 'PROCESANDO'
            }
        )
        
    table.update_item(
        Key={'tenant_rfc': tenant_rfc},
        UpdateExpression="SET estatus_global = :s, porcentaje_avance = :p",
        ExpressionAttributeValues={':s': 'COMPLETO', ':p': 100}
    )

    return {"status": "FINISHED", "count": len(archivos_a_esculpir)}
