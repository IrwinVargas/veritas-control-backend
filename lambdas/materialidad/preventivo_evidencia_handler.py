# lambdas/materialidad/preventivo_evidencia_handler.py
import os
import json
import io
import boto3
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    headers = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type,Authorization', 'Access-Control-Allow-Methods': 'POST,OPTIONS'}
    if event.get('httpMethod') == 'OPTIONS': return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        tenant_id = authorizer.get('custom:tenant_id')

        body = json.loads(event.get('body', '{}'))
        rfc_cliente = body.get('rfc')

        hash_key = f"{tenant_id}#{rfc_cliente.upper().strip()}"
        table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE'))
        expediente_item = table.get_item(Key={'tenant_rfc': hash_key}).get('Item', {})
        lista_productos = expediente_item.get('catalogo_benchmarking', [])

        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
        styles = getSampleStyleSheet()
        style_title = ParagraphStyle('T', fontName='Helvetica-Bold', fontSize=14, leading=18, textColor='#16a34a', alignment=TA_CENTER, spaceAfter=20)
        style_desc = ParagraphStyle('D', fontName='Helvetica', fontSize=10, leading=14, textColor='#475569', spaceAfter=15)

        story = [Paragraph("REPOSITORIO MAESTRO DE EVIDENCIAS DIGITALES DE MATERIALIDAD", style_title), Spacer(1, 10)]

        # Barremos los mapas NoSQL para incrustar las fotos reales que subió el cliente
        conteo_imagenes = 0
        if isinstance(lista_productos, list):
            for p in lista_productos:
                key_foto = p.get('key_imagen_s3', '')
                if key_foto:
                    try:
                        obj_f = s3_client.get_object(Bucket=os.environ.get('BUCKET_NAME'), Key=key_foto)
                        story.append(Paragraph(f"Evidencia Tangible de Solución: {p.get('amplitud_linea', 'Concepto')}", style_desc))
                        story.append(Image(io.BytesIO(obj_f['body'].read()), width=200, height=180))
                        story.append(Spacer(1, 20))
                        conteo_imagenes += 1
                    except Exception: pass

        if conteo_imagenes == 0:
            story.append(Paragraph("No se localizaron capturas o evidencias multimedia adjuntas en el catálogo NoSQL para este periodo.", style_desc))

        doc.build(story)
        pdf_buffer.seek(0)

        # 🚀 ALMACENAMIENTO BAHO LA SUB CARPETA 04 EVIDENCIA DIGITAL
        bucket_name = os.environ.get('BUCKET_NAME')
        s3_key_final = f"{tenant_id}/{rfc_cliente}/1. Análisis Benchmarking Competitivo/04 Evidencia Digital/03 Evidencia Crono, Memo Y Carta/Evidencia_Crono_Memo_Y_Carta.pdf"
        s3_client.put_object(Bucket=bucket_name, Key=s3_key_final, Body=pdf_buffer.read(), ContentType='application/pdf')

        url_firmada = s3_client.generate_presigned_url(ClientMethod='get_object', Params={'Bucket': bucket_name, 'Key': s3_key_final}, ExpiresIn=1800)

        table.update_item(
            Key={'tenant_rfc': hash_key},
            UpdateExpression="SET archivos.evidencia = :e, estatus_expediente = :s, fase_actual = :f",
            ExpressionAttributeValues={
                ':s': 'COMPLETO', ':f': 'FINALIZADO',
                ':e': {"status": "COMPLETO", "s3_key": s3_key_final, "download_url": url_firmada, "updated_at": datetime.utcnow().isoformat() + "Z"}
            }
        )

        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'success': True, 'download_url': url_firmada})}
    except Exception as e:
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
