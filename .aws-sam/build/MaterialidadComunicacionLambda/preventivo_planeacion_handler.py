import os
import json
import io
import boto3
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib import colors

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
        comp_nacional = body.get('competencia_nacional', 'HENKEL')
        comp_inter = body.get('competencia_internacional', 'QUÍMICA DELTA')

        # 🧠 MONTO Y LÓGICA FINANCIERA DEL DOCUMENTO ADJUNTO
        subtotal = 1609562.93
        iva = subtotal * 0.16
        total = subtotal + iva

        # MAQUETACIÓN EDITORIAL DE ALTA FIDELIDAD (ReportLab GRID Canvas)
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        
        style_cell = ParagraphStyle('CellText', fontName='Helvetica', fontSize=8, leading=11, textColor='#1e293b')
        style_cell_bold = ParagraphStyle('CellTextB', fontName='Helvetica-Bold', fontSize=8, leading=11, textColor='#1e293b')
        style_header = ParagraphStyle('HeadText', fontName='Helvetica-Bold', fontSize=9, leading=12, textColor='#1e293b', alignment=TA_CENTER)

        # CONFECCIÓN DE LA MATRIZ DE RECHART CONTABLE (Datos de tu adjunto)
        data_tabla = [
            [Paragraph("EMPRESA", style_header), Paragraph("CONCEPTO", style_header), Paragraph("ACTIVIDAD", style_header), Paragraph("MONTO", style_header), Paragraph("PERIODO", style_header)],
            [
                Paragraph(f"<strong>{bufete_nombre.upper()}</strong>", style_cell),
                Paragraph("80141500<br/>ANÁLISIS BENCHMARKING COMPETITIVO", style_cell),
                Paragraph(f"• Planificación estratégica.<br/>• Desarrollo de benchmarking enfocado en {comp_nacional} y {comp_inter} para conocer su posicionamiento digital y matrices BCG.", style_cell),
                Paragraph(f"${subtotal:,.2f}", style_cell_bold),
                Paragraph("ENERO - DICIEMBRE FISCAL", style_cell)
            ],
            [Paragraph("", style_cell), Paragraph("", style_cell), Paragraph("SUBTOTAL", style_header), Paragraph(f"${subtotal:,.2f}", style_cell_bold), " "],
            [Paragraph("", style_cell), Paragraph("", style_cell), Paragraph("IVA (16%)", style_header), Paragraph(f"${iva:,.2f}", style_cell_bold), " "],
            [Paragraph("", style_cell), Paragraph("", style_cell), Paragraph("TOTAL", style_header), Paragraph(f"${total:,.2f}", style_cell_bold), " "]
        ]

        t = Table(data_tabla, colWidths=[100, 100, 210, 70, 60])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8fafc')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,0), 1, colors.HexColor('#cbd5e1')),
            ('GRID', (0,1), (-1,1), 1, colors.HexColor('#cbd5e1')),
            ('LINEBELOW', (2,2), (3,4), 1, colors.HexColor('#cbd5e1')),
            ('BACKGROUND', (2,2), (2,4), colors.HexColor('#f8fafc')),
        ]))

        story = [Paragraph(f"<strong>REPORTE DE SEGUIMIENTO Y CONTROL ADMINISTRATIVO</strong>", style_header), Spacer(1, 15), t]
        doc.build(story)
        
        pdf_buffer.seek(0)
        s3_key = f"{tenant_id}/{rfc_cliente}/1. Análisis Benchmarking Competitivo/01 Planeación/01 Benchmarking_Competitivo.pdf"
        s3_client.put_object(Bucket=os.environ.get('BUCKET_NAME'), Key=s3_key, Body=pdf_buffer.read(), ContentType='application/pdf')

        # Actualizamos NoSQL mudando la fase a la Etapa 3 (Comunicación)
        hash_key = f"{tenant_id}#{rfc_cliente.upper().strip()}"
        dynamodb.Table(os.environ.get('DYNAMODB_TABLE')).update_item(
            Key={'tenant_rfc': hash_key},
            UpdateExpression="SET archivos.benchmarking = :b, fase_actual = :f",
            ExpressionAttributeValues={
                ':f': 'COMUNICACION',
                ':b': {"status": "COMPLETO", "s3_key": s3_key, "updated_at": datetime.utcnow().isoformat() + "Z"}
            }
        )

        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'success': True, 's3_key': s3_key})}
    except Exception as e:
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
