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
        print("🎨 Paso 3: Inicializando maquetación robusta y editorial premium...")
        
        tenant_id = event.get('tenant_id')
        rfc_cliente = event.get('rfc_cliente')
        nombre_cliente = event.get('nombre_cliente')
        ano_fiscal = event.get('ano_fiscal', str(datetime.now().year))
        contrato = event.get('contrato', 'PRESTACION_SERVICIOS')
        texto_ia_crudo = event.get('texto_pericial', '')
        catalogo_json = event.get('catalogo_json_payload', [])

        bucket_name = os.environ.get('BUCKET_NAME', 'veritas-control-materialidad-expedientes-dev')
        table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'veritas-control-materialidad-status-dev'))
        hash_key = f"{tenant_id}#{rfc_cliente}#{contrato}#{ano_fiscal}"

        # Compilación en memoria RAM
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer, pagesize=letter,
            rightMargin=45, leftMargin=45, topMargin=110, bottomMargin=75
        )
        
        styles = getSampleStyleSheet()
        
        # ⚙️ RE-CALIBRACIÓN ESTRICTA DE TIPOGRAFÍAS EXECUTIVE
        style_logo_title = ParagraphStyle('LogoT', fontName='Helvetica-Bold', fontSize=15, leading=18, textColor='#1e293b', spaceAfter=2)
        style_logo_sub = ParagraphStyle('LogoS', fontName='Helvetica', fontSize=8, leading=10, textColor='#a18262', alignment=TA_LEFT)
        style_date_meta = ParagraphStyle('DateM', fontName='Helvetica', fontSize=10, leading=14, textColor='#475569', alignment=TA_RIGHT, spaceAfter=25)
        
        style_saludo = ParagraphStyle('Saludo', fontName='Helvetica-Bold', fontSize=11, leading=15, textColor='#1e293b', spaceAfter=14)
        style_body_legal = ParagraphStyle('BodyL', fontName='Helvetica', fontSize=10, leading=16, textColor='#334155', alignment=TA_JUSTIFY, spaceAfter=12)
        
        style_th = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor='#ffffff', alignment=TA_CENTER)
        style_td = ParagraphStyle('TD', fontName='Helvetica', fontSize=9, leading=12, textColor='#1e293b')

        story = []

        # 1. ENCABEZADO SIMÉTRICO: Logotipo Veritas & Slogan (Lado Izquierdo)
        story.append(Paragraph("VERITAS CONTROL", style_logo_title))
        story.append(Paragraph("SUITE DE BLINDAJE JURÍDICO E INMUTABILIDAD FISCAL", style_logo_sub))
        story.append(Spacer(1, 15))

        # 2. FECHA DINÁMICA (Idéntica a la posición de la imagen de referencia)
        fecha_str = f"Ciudad de México, a {datetime.now().strftime('%d de %B de %Y')}"
        story.append(Paragraph(f"<b>Fecha:</b> {fecha_str}<br/><b>Ejercicio Evaluado:</b> {ano_fiscal}", style_date_meta))

        # 3. DESTINATARIO COMPUESTO ROBUSTO
        story.append(Paragraph(f"A quien corresponda:<br/>Representante Legal / Consejo de Administración de {nombre_cliente}", style_saludo))

        # =========================================================================
        # 🛡️ CLÁUSULAS ROBUSTAS DE MÁXIMA DEFECTOLOGÍA LEGAL (ANTI-HUECOS DEL SAT)
        # =========================================================================
        p1_sat = """
        <b>PRIMERO. SUSTENTO Y FUNDAMENTO LEGAL.</b> El presente instrumento científico pericial constituye la manifestación expresa de la materialidad de operaciones celebradas, instrumentado bajo los estrictos lineamientos del <b>Artículo 69-B del Código Fiscal de la Federación (CFF)</b> en vigor [finance]. Se hace constar que el prestador del servicio cuenta con la infraestructura tecnológica instalada, capacidad humana directa, activos fijos debidamente inventariados y solvencia operativa real para devengar las soluciones que amparan los flujos comerciales de este ejercicio contable, desvirtuando cualquier presunción de inexistencia o simulación de actos jurídicos por parte de la autoridad hacendaria [finance].
        """
        story.append(Paragraph(p1_sat, style_body_legal))

        # Injectamos el texto generado por Claude 4.5 Haiku purificado
        if texto_ia_crudo:
            for block in texto_ia_crudo.split('\n'):
                clean_block = block.strip().replace('#', '').replace('*', '')
                if clean_block:
                    story.append(Paragraph(clean_block, style_body_legal))
        else:
            p2_fallback = f"<b>SEGUNDO. VALIDACIÓN DE ENTREGABLES JURÍDICOS.</b> Se certifica la entrega secuencial cronológica de los insumos comerciales, reportes de benchmarking de mercado, validación de controles internos y bitácoras operativas correspondientes al contrato de naturaleza {contrato.replace('_', ' ')}."
            story.append(Paragraph(p2_fallback, style_body_legal))

        story.append(Spacer(1, 15))

        # 4. MATRIZ EN TABLA CEBRA TOTALMENTE SELLADA
        t_data = [[Paragraph("Evidencia Multimedia", style_th), Paragraph("Descripción de la Solución Devengada", style_th), Paragraph("Valor de Mercado", style_th)]]
        for prod in catalogo_json:
            img_obj = "—"
            if prod.get('key_foto'):
                try:
                    obj_f = s3_client.get_object(Bucket=bucket_name, Key=prod['key_foto'])
                    img_obj = Image(io.BytesIO(obj_f['body'].read()), width=40, height=35)
                except Exception: pass
            t_data.append([img_obj, Paragraph(prod['desc'], style_td), Paragraph(f"$ {prod['precio']:,.2f} MXN", style_td)])

        tabla_forense = Table(t_data, colWidths=[110, 310, 100])
        tabla_forense.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')), 
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]) 
        ]))
        story.append(tabla_forense)
        story.append(Spacer(1, 35))

        # =========================================================================
        # ✍️ PANEL DE FIRMAS EXHAUSTIVO (Look de la Imagen Adjunta)
        # =========================================================================
        Firma_Bloque = []
        Firma_Bloque.append(Paragraph("<b>PROTESTO LO NECESARIO Y DECLARO BAJO PROTESTA DE DECIR VERDAD</b>", ParagraphStyle('F1', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor='#64748b', alignment=TA_LEFT, spaceAfter=20)))
        
        # Simulación de la firma manuscrita cursiva de la foto
        Firma_Bloque.append(Paragraph("<i>Edward Richard</i>", ParagraphStyle('FirmaCursiva', fontName='Times-Italic', fontSize=18, leading=20, textColor='#1e3a8a', spaceAfter=2)))
        Firma_Bloque.append(Paragraph("________________________________________", ParagraphStyle('Linea', fontName='Helvetica', fontSize=10, leading=12, textColor='#cbd5e1', spaceAfter=4)))
        Firma_Bloque.append(Paragraph("<b>EDWARD RICHARD</b>", ParagraphStyle('Name', fontName='Helvetica-Bold', fontSize=10, leading=12, textColor='#1e293b')))
        Firma_Bloque.append(Paragraph(f"Socio Director / Perito Dictaminador de Materialidad<br/>Ecosistema Veritas Multi-Tenant ID: {tenant_id}", ParagraphStyle('Puesto', fontName='Helvetica', fontSize=8, leading=11, textColor='#64748b')))
        
        # Usamos KeepTogether para garantizar que el bloque de firmas jamás se quede huérfano cortado a la mitad
        story.append(KeepTogether(Firma_Bloque))

        # Construcción formal amarrada al CanvasMaker estilizado de la imagen
        doc.build(story, canvasmaker=CanvasPapelMembretadoVeritas)
        pdf_buffer.seek(0)
        pdf_bytes = pdf_buffer.read()

        # Volcado indexado en Amazon S3
        s3_key_final = f"{tenant_id}/{rfc_cliente}/{ano_fiscal}/{contrato}/02 Materialidad/01 Libro_Forense_Consolidado.pdf"
        s3_client.put_object(Bucket=bucket_name, Key=s3_key_final, Body=pdf_bytes, ContentType='application/pdf')

        url_firmada = s3_client.generate_presigned_url(ClientMethod='get_object', Params={'Bucket': bucket_name, 'Key': s3_key_final}, ExpiresIn=1800)

        # Marcamos el 100% de éxito en tu tabla maestra NoSQL de materialidad status
        table.update_item(
            Key={'tenant_rfc_year_contract': hash_key},
            UpdateExpression="SET progreso_porcentaje = :p, estatus_global = :e, mensaje_progreso = :m, archivos.materialidad = :file_obj",
            ExpressionAttributeValues={
                ':p': 100, ':e': 'COMPLETO', ':m': "¡Expediente Forense Completo y Sellado con Éxito!",
                ':file_obj': {"status": "COMPLETO", "s3_key": s3_key_final, "download_url": url_firmada, "updated_at": datetime.utcnow().isoformat() + "Z"}
            }
        )
        print(f"🎯 PDF Robusto con Look de Muestra inyectado con éxito en S3: {s3_key_final}")
        return {"status": "FINISHED"}