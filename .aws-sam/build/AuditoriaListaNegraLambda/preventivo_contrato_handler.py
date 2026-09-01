import os
import json
import io
import boto3
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.pdfgen import canvas

bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

class CanvasNumeradoContrato(canvas.Canvas):
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
            self.draw_footer(page_count)
            super().showPage()
        super().save()

    def draw_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor("#64748b")
        # Línea sutil perimetral superior del pie de página
        self.setStrokeColor("#e2e8f0")
        self.setLineWidth(0.5)
        self.line(54, 40, 558, 40)
        
        # Leyenda de confidencialidad institucional del bufete
        texto_privacidad = "CONTRATO PRIVADO DE PRESTACIÓN DE SERVICIOS - ESTRICTAMENTE CONFIDENCIAL"
        self.drawString(54, 28, texto_privacidad)
        
        # Paginador automatizado alineado al extremo derecho
        paginacion = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(558, 28, paginacion)
        self.restoreState()

def handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }

    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        print("Inicializando Asistente de Redacción Preventiva Contractual...")
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        
        tenant_id = authorizer.get('custom:tenant_id')
        bufete_nombre = authorizer.get('custom:company_name', 'EL PRESTADOR DE SERVICIOS')
        bufete_rfc = authorizer.get('custom:company_rfc', 'XAXX010101000')

        body = json.loads(event.get('body', '{}'))
        rfc_cliente = body.get('rfc')
        nombre_cliente = body.get('nombre')
        
        objeto_servicio = body.get('objeto_servicio')
        monto_mensual = body.get('monto_mensual')
        vigencia_meses = body.get('vigencia_meses', '12')

        if not tenant_id or not rfc_cliente or not objeto_servicio:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'Formulario de acompañamiento incompleto.'})}

        prompt_guiado = f"""
        Humano: Actúa como un prestigiado Abogado Corporativo y Notario en México. 
        Redacta de forma formal, rigurosa y elegante el cuerpo de CLÁUSULAS de un Contrato Privado de Prestación de Servicios Profesionales.
        
        LINEAMIENTOS DEL NEGOCIO:
        - Prestador: {bufete_nombre.upper()} (RFC: {bufete_rfc.upper()}).
        - Cliente: "{nombre_cliente}" (RFC: "{rfc_cliente}").
        - Objeto del Servicio: "{objeto_servicio}".
        - Precio / Contraprestación: {monto_mensual} MXN mensuales.
        - Vigencia: {vigencia_meses} meses.

        REQUISITOS DE REDACCIÓN:
        1. Comienza directamente con la sección de "CLAUSULAS" (Asume que el Proemio y Declaraciones ya fueron redactados arriba).
        2. Cláusula Primera (Objeto): Detalla de forma exhaustiva los entregables tangibles, el personal activo calificado y la infraestructura administrativa que el Prestador utilizará para cumplir el acuerdo.
        3. Cláusula Segunda (Precio y Forma de Pago): Especifica la contraprestación de {monto_mensual} MXN, la obligación de emitir el comprobante fiscal (CFDI) correspondiente y los tiempos de pago.
        4. Cláusula Tercera (Vigencia): Fija la duración en {vigencia_meses} meses ininterrumpidos.
        5. Cláusula Cuarta (Confidencialidad y Licitud de Recursos): Incluye una sección estricta alineada a la Ley de Extinción de Dominio garantizando que el origen de los fondos es lícito.

        Usa lenguaje solemne, legal y preciso. No incluyas notas de autor, comentarios, ni menciones la palabra "materialidad" o "inteligencia artificial". Redacta solo el articulado de cláusulas.
        Asistente:
        """

        model_id = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

        body_payload = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2500,
            "temperature": 0.1,
            "messages": [{"role": "user", "content": prompt_guiado}]
        })

        print(f"Invocando API de Amazon Bedrock usando Inferencia Universal: {model_id}...")
        
        response = bedrock_runtime.invoke_model(
            body=body_payload,
            modelId=model_id,
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response.get('body').read())
        contenido_bloques = response_body.get('content', [])
        if isinstance(contenido_bloques, list) and len(contenido_bloques) > 0:
            texto_clausulas = contenido_bloques[0].get('text', '')
        else:
            texto_clausulas = response_body.get('content', {}).get('text', '')

        print("Éxito: Análisis de materialidad contractual redactado por Claude con éxito.")

        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
        
        styles = getSampleStyleSheet()
        style_header_doc = ParagraphStyle('HeaderDoc', fontName='Helvetica-Bold', fontSize=14, leading=18, textColor='#1e3a8a', alignment=TA_CENTER, spaceAfter=20)
        style_seccion = ParagraphStyle('SeccionLegal', fontName='Helvetica-Bold', fontSize=11, leading=14, textColor='#0f172a', spaceBefore=12, spaceAfter=8, alignment=TA_LEFT)
        style_cuerpo_legal = ParagraphStyle('CuerpoLegal', fontName='Helvetica', fontSize=10, leading=15, textColor='#334155', alignment=TA_JUSTIFY, spaceAfter=10)

        story = []
        
        # 📄 PROEMIO Y DECLARACIONES DINÁMICAS
        story.append(Paragraph("CONTRATO DE PRESTACIÓN DE SERVICIOS PROFESIONALES", style_header_doc))
        
        proemio_text = (
            f"CONTRATO DE PRESTACIÓN DE SERVICIOS QUE CELEBRAN POR UNA PARTE, {bufete_nombre.upper()}, "
            f"REPRESENTADA EN ESTE ACTO POR SU APODERADO LEGAL (EN LO SUCESIVO EL \"PRESTADOR\"); "
            f"Y POR LA OTRA PARTE, {nombre_cliente.upper()}, REPRESENTADA POR SU APODERADO LEGAL (EN LO SUCESIVO EL \"CLIENTE\"), "
            f"AL TENOR DE LAS SIGUIENTES DECLARACIONES Y CLÁUSULAS:"
        )
        story.append(Paragraph(proemio_text, style_cuerpo_legal))
        story.append(Spacer(1, 10))

        story.append(Paragraph("DECLARACIONES", style_seccion))
        
        declara_prestador = (
            f"<strong>I. Declara el PRESTADOR, por conducto de su apoderado legal:</strong><br/>"
            f"a) Que es una persona moral debidamente constituida y registrada conforme a las leyes de los Estados Unidos Mexicanos.<br/>"
            f"b) Que cuenta con la clave del Registro Federal de Contribuyentes número <strong>{bufete_rfc.upper()}</strong>.<br/>"
            f"c) Que cuenta con la infraestructura tecnológica, activos, capacidad técnica y administrativa suficiente para cumplir cabalmente con las obligaciones del presente instrumento."
        )
        story.append(Paragraph(declara_prestador, style_cuerpo_legal))
        
        declara_cliente = (
            f"<strong>II. Declara el CLIENTE, por conducto de su representante:</strong><br/>"
            f"a) Que es una entidad legalmente constituida y con capacidad jurídica plena para celebrar y obligarse bajo los términos de este contrato.<br/>"
            f"b) Que cuenta con el Registro Federal de Contribuyentes número <strong>{rfc_cliente.upper()}</strong> y requiere la prestación de los servicios especializados del PRESTADOR."
        )
        story.append(Paragraph(declara_cliente, style_cuerpo_legal))
        story.append(Spacer(1, 10))

        story.append(Paragraph("CLÁUSULAS", style_header_doc))
        
        for parrafo in texto_clausulas.split('\n'):
            clean_p = parrafo.strip()
            if not clean_p: continue
            if clean_p.upper().startswith(("PRIMERA", "SEGUNDA", "TERCERA", "CUARTA", "QUINTA", "CLÁUSULA", "CLAUSULA")):
                story.append(Paragraph(clean_p, style_seccion))
            else:
                story.append(Paragraph(clean_p, style_cuerpo_legal))

        doc.build(story, canvasmaker=CanvasNumeradoContrato)
        pdf_buffer.seek(0)
        pdf_bytes = pdf_buffer.read()

        bucket_name = os.environ.get('BUCKET_NAME')
        s3_key_preventivo = f"{tenant_id}/{rfc_cliente}/0. Contrato/01. Contrato.pdf"
        s3_client.put_object(Bucket=bucket_name, Key=s3_key_preventivo, Body=pdf_bytes, ContentType='application/pdf')

        url_descarga_firmada = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': bucket_name, 'Key': s3_key_preventivo},
            ExpiresIn=1800
        )
        
        hash_key = f"{tenant_id}#{rfc_cliente.upper().strip()}"
        table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE'))
        
        table.update_item(
            Key={'tenant_rfc': hash_key},
            UpdateExpression="SET archivos = if_not_exists(archivos, :empty_map), estatus_expediente = :global_status, tipo_strategy = :strat, fase_actual = :fase",
            ExpressionAttributeValues={':empty_map': {}, ':global_status': 'PROCESANDO', ':strat': 'PREVENTIVO', ':fase': 'PLANEACION'}
        )
        table.update_item(
            Key={'tenant_rfc': hash_key},
            UpdateExpression="SET archivos.contrato = :c",
            ExpressionAttributeValues={':c': {"status": "COMPLETO", "s3_key": s3_key_preventivo, "updated_at": datetime.utcnow().isoformat() + "Z"}}
        )

        print("🎯 Éxito: Fase 1 Preventiva guardada y sellada de forma documental NoSQL.")
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True, 
                'message': 'Contrato generado e inyectado al workflow preventivo NoSQL.',
                'download_url': url_descarga_firmada
            })
        }
    except Exception as e:
        print(f"❌ Crash en inyector preventivo contractual: {str(e)}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
