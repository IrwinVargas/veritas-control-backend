# lambdas/materialidad/preventivo_comunicacion_handler.py
import os
import json
import io
import boto3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    headers = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type,Authorization', 'Access-Control-Allow-Methods': 'POST,OPTIONS'}
    if event.get('httpMethod') == 'OPTIONS': return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        tenant_id = authorizer.get('custom:tenant_id')
        bufete_nombre = authorizer.get('custom:company_name', 'CA CONTADORES Y ABOGADOS')

        body = json.loads(event.get('body', '{}'))
        rfc_cliente = body.get('rfc')
        nombre_cliente = body.get('nombre')
        bimestre = int(body.get('bimestre', 1))

        mapa_periodos = {
            1: "Enero_Febrero", 2: "Marzo_Abril", 3: "Mayo_Junio",
            4: "Julio_Agosto", 5: "Septiembre_Octubre", 6: "Noviembre_Diciembre"
        }
        periodo_str = mapa_periodos.get(bimestre, "Periodo_General")

        # 🧠 PROMPT PARA LA REDACCIÓN DE MEMORÁNDUMS Y CARTAS DE ACEPTACIÓN
        prompt = f"""
        Humano: Actúa como un experto en control interno corporativo en México. 
        Redacta una Solicitud de Cotización formal emitida por el cliente {nombre_cliente} hacia {bufete_nombre}, 
        seguida de un Memorándum de Trabajo para el periodo {periodo_str.replace('_', ' ')}.
        No uses marcas Markdown como # o *. Comienza directo con el texto.
        Asistente:
        """

        body_payload = json.dumps({"anthropic_version": "bedrock-2023-05-31", "max_tokens": 1500, "temperature": 0.1, "messages": [{"role": "user", "content": prompt}]})
        response = bedrock_runtime.invoke_model(body=body_payload, modelId="us.anthropic.claude-haiku-4-5-20251001-v1:0", accept="application/json", contentType="application/json")
        texto_comunicacion = json.loads(response.get('body').read()).get('content', [{}])['text'].replace('#', '').replace('*', '').strip()

        # Compilación en ReportLab RAM
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
        styles = getSampleStyleSheet()
        style_title = ParagraphStyle('T', fontName='Helvetica-Bold', fontSize=12, leading=15, textColor='#0284c7', alignment=TA_CENTER, spaceAfter=15)
        style_body = ParagraphStyle('B', fontName='Helvetica', fontSize=10, leading=14, textColor='#334155', alignment=TA_JUSTIFY, spaceAfter=8)

        story = [Paragraph(f"EVIDENCIA DE COMUNICACIÓN EMPRESARIAL - BIMESTRE {bimestre}", style_title), Spacer(1, 10)]
        for line in texto_comunicacion.split('\n'):
            if line.strip(): story.append(Paragraph(line.strip(), style_body))

        doc.build(story)
        pdf_buffer.seek(0)
        pdf_bytes = pdf_buffer.read()

        # 🚀 ALMACENAMIENTO EXACTO EN LA SUB CARPETA 03 SOLICITUD DE COTIZACIÓN
        bucket_name = os.environ.get('BUCKET_NAME')
        s3_key_solicitud = f"{tenant_id}/{rfc_cliente}/1. Análisis Benchmarking Competitivo/03 Comunicación Empresarial/0 Solicitud de Cotización/0{bimestre} Solicitud_{periodo_str}.pdf"
        s3_client.put_object(Bucket=bucket_name, Key=s3_key_solicitud, Body=pdf_bytes, ContentType='application/pdf')

        # 🚀 ALMACENAMIENTO EXACTO EN LA SUB CARPETA 03 MEMORÁNDUMS
        s3_key_memo = f"{tenant_id}/{rfc_cliente}/1. Análisis Benchmarking Competitivo/03 Comunicación Empresarial/03 Memorándums/Memorandum_{200+bimestre}_{periodo_str}_2026.pdf"
        s3_client.put_object(Bucket=bucket_name, Key=s3_key_memo, Body=pdf_bytes, ContentType='application/pdf')

        url_firmada = s3_client.generate_presigned_url(ClientMethod='get_object', Params={'Bucket': bucket_name, 'Key': s3_key_memo}, ExpiresIn=1800)

        # Actualizamos la base NoSQL
        hash_key = f"{tenant_id}#{rfc_cliente.upper().strip()}"
        dynamodb.Table(os.environ.get('DYNAMODB_TABLE')).update_item(
            Key={'tenant_rfc': hash_key},
            UpdateExpression="SET archivos.comunicacion = :c, fase_actual = :f",
            ExpressionAttributeValues={
                ':f': 'EVIDENCIA',
                ':c': {"status": "COMPLETO", "s3_key": s3_key_memo, "download_url": url_firmada, "updated_at": datetime.utcnow().isoformat() + "Z"}
            }
        )

        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'success': True, 'download_url': url_firmada})}
    except Exception as e:
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
