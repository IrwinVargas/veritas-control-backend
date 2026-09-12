# =========================================================================
# MICROSERVICIO FINAL: ESCULTOR VECTORIAL POLIMÓRFICO EN LOTE (4 SECCIONES)
# RUTA EN MAC: lambdas/materialidad/step3_escultor_handler.py
# =========================================================================
import os
import io
import json
import boto3
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib import colors

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    print("🎨 Paso 3 Activo: Iniciando la Fábrica de Renderizado ReportLab en Lote...")
    
    tenant_id = event.get('tenant_id', 'bufete-veritas-uuid-1111')
    rfc_cliente = event.get('rfc_cliente', '')
    ano_fiscal = event.get('ano_fiscal', '2026')
    
    # Recuperamos la partición compuesta NoSQL única obligatoria de tu esquema
    tenant_rfc = event.get('tenant_rfc', f"{tenant_id}#{rfc_cliente}")
    
    # Succionamos el array de documentos redactados por el Paso 2 (Strategy)
    archivos_a_esculpir = event.get('archivos_redactados_ia', [])
    
    bucket_name = os.environ.get('BUCKET_NAME', 'veritas-control-materialidad-dev')
    nombre_tabla = os.environ.get('NOTIFICACIONES_TABLE', 'veritas-control-materialidad-nosql-dev')
    table = dynamodb.Table(nombre_tabla)

    # 🚀 PATRÓN ITERADOR: Procesa y sella cada documento de forma independiente
    for doc in archivos_a_esculpir:
        nombre_file = doc["nombre_archivo"]
        folder_sat = doc["folder_seccion"]
        prosa_ia = doc["prosa_completa_ia"]

        # Inicializamos el lienzo en memoria RAM
        pdf_buffer = io.BytesIO()
        doc_template = SimpleDocTemplate(
            pdf_buffer, pagesize=letter,
            rightMargin=45, leftMargin=45, topMargin=110, bottomMargin=75
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Estilo de prosa corporativa ROUCHERS
        style_legal_body = ParagraphStyle(
            'DynamicLegalBody', fontName='Helvetica', fontSize=9.5, leading=16,
            textColor=colors.HexColor("#334155"), alignment=TA_JUSTIFY, spaceAfter=12
        )

        # Inyectamos los párrafos generados por la IA de principio a fin (Títulos a Firmas)
        for parrafo in prosa_ia.split('\n'):
            if parrafo.strip():
                story.append(Paragraph(parrafo.strip(), style_legal_body))

        # Compilación vectorial del PDF
        doc_template.build(story)
        pdf_buffer.seek(0)
        pdf_bytes_reales = pdf_buffer.getvalue()

        # 📐 COORDENADA MULTIDIMENSIONAL EXACTA EN S3 (Dividida por tus 4 Carpetas SAT)
        s3_key_pdf = f"{tenant_id}/{rfc_cliente}/{ano_fiscal}/{folder_sat}/{nombre_file}"
        
        print(f"📡 Sembrando archivo binario en Amazon S3: [{s3_key_pdf}]")
        s3_client.put_object(
            Bucket=str(bucket_name).strip(),
            Key=s3_key_pdf,
            Body=pdf_bytes_reales,
            ContentType='application/pdf'
        )
        pdf_buffer.close()

        # =========================================================================
        # ⚡ DESCARGA EN CALIENTE PARCIAL (INCREMENTAL NoSQL DYNAMODB)
        # Mapeamos el nombre del archivo a una clave limpia para actualizar DynamoDB
        # permitiendo que el Front habilite la descarga de este PDF de inmediato.
        # =========================================================================
        campo_db_dinamico = nombre_file.lower().replace(".pdf", "")
        
        print(f"💾 Actualizando bandera parcial en DynamoDB para el campo: {campo_db_dinamico}...")
        table.update_item(
            Key={'tenant_rfc': tenant_rfc},
            UpdateExpression=f"SET {campo_db_dinamico} = :m, estatus_global = :s",
            ExpressionAttributeValues={
                ':m': {
                    'status': 'COMPLETO',
                    'download_url': f"https://{bucket_name}://{s3_key_pdf}",
                    'packaged_at': datetime.utcnow().isoformat()
                },
                ':s': 'PROCESANDO'
            }
        )

    # =========================================================================
    # 🏁 CIERRE DEL LOTE TOTAL: Sella el estatus global a COMPLETO al 100%
    # =========================================================================
    print("🎯 Lote de cumplimiento SAT completado con éxito absoluto.")
    table.update_item(
        Key={'tenant_rfc': tenant_rfc},
        UpdateExpression="SET estatus_global = :s, porcentaje_avance = :p",
        ExpressionAttributeValues={
            ':s': 'COMPLETO',
            ':p': 100
        }
    )

    return {"status": "FINISHED", "count": len(archivos_a_esculpir)}
