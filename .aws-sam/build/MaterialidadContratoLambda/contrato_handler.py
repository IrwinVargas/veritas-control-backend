# backend/lambdas/materialidad/contrato_handler.py
import os
import json
import io
import boto3
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY

bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    try:
        tenant_id = event.get('tenant_id', 'bufete-default')
        rfc_cliente = event.get('rfc_cliente', 'DESCONOCIDO')
        nombre_cliente = event.get('nombre_cliente', 'Cliente Anonimo')
        bucket_destino = os.environ.get('BUCKET_NAME')

        hash_key = f"{tenant_id}#{rfc_cliente}"
        table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE') or "certeza-control-materialidad-status-dev")

        print("Asegurando la estructura del contenedor padre y la estrategia en DynamoDB NoSQL...")
        table.update_item(
            Key={'tenant_rfc': hash_key},
            UpdateExpression="SET archivos = if_not_exists(archivos, :empty_map), estatus_expediente = :global_status, tipo_strategy = :strat",
            ExpressionAttributeValues={
                ':empty_map': {},
                ':global_status': 'PROCESANDO',
                ':strat': 'RECONSTRUCCION' # <-- Agrega esta línea inmutable clave
            }
        )

        print("Notificando arranque de fase contractual...")
        table.update_item(
            Key={'tenant_rfc': hash_key},
            UpdateExpression="SET archivos.contrato = :c",
            ExpressionAttributeValues={
                ':c': {
                    "status": "PROCESANDO",
                    "s3_key": None,
                    "updated_at": datetime.utcnow().isoformat() + "Z"
                }
            }
        )

        # INVOCACIÓN EN REDUNDANCIA DE MODELOS A CLAUDE 4.5 HAIKU
        prompt = f"Actúa como perito legal. Genera las cláusulas de materialidad contractual para {nombre_cliente}..."
        body_payload = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": prompt}]
        })

        response = bedrock_runtime.invoke_model(
            body=body_payload,
            modelId="us.anthropic.claude-haiku-4-5-20251001-v1:0",
            accept="application/json", contentType="application/json"
        )
        response_body = json.loads(response.get('body').read())
        contenido_bloques = response_body.get('content', [])
        if isinstance(contenido_bloques, list) and len(contenido_bloques) > 0:
            texto_legal = contenido_bloques[0].get('text', '')
        else:
            texto_legal = response_body.get('content', {}).get('text', '')

        print("Éxito: Análisis de materialidad contractual redactado por Claude con éxito.")

        # COMPILACIÓN EDITORIAL DEL PDF EN MEMORIA RAM
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        style_cuerpo = ParagraphStyle('C', parent=styles['Normal'], fontSize=11, leading=16, alignment=TA_JUSTIFY)
        story = [Paragraph("DIKTAMEN PERICIAL CONTRACTUAL DE RECONSTRUCCIÓN", style_cuerpo), Spacer(1, 15)]
        for p in texto_legal.split('\n'):
            if p.strip(): story.append(Paragraph(p.strip(), style_cuerpo))
        doc.build(story)
        pdf_buffer.seek(0)

        # VOLCADO BINARIO DIRECTO A S3
        s3_key_final = f"{tenant_id}/{rfc_cliente}/reconstruccion/contrato_clausulas.pdf"
        s3_client.put_object(Bucket=bucket_destino, Key=s3_key_final, Body=pdf_buffer.read(), ContentType='application/pdf')

        # NOTIFICACIÓN DE CIERRE: Sellamos de forma atómica en DynamoDB que este PDF ya está disponible
        print("Sellando fase contractual como COMPLETA...")
        table.update_item(
            Key={'tenant_rfc': hash_key},
            UpdateExpression="SET archivos.contrato = :c",
            ExpressionAttributeValues={
                ':c': {
                    "status": "COMPLETO",
                    "s3_key": s3_key_final,
                    "updated_at": datetime.utcnow().isoformat() + "Z"
                }
            }
        )

        return {"status": "COMPLETO", "s3_key": s3_key_final}
    except Exception as e:
        print(f"❌ Error asíncrono en rama contratos: {str(e)}")
        raise e
