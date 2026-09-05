import os
import json
import io
import boto3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib import colors

bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

class CanvasLibroCorporativo(canvas.Canvas):
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
                # Cintillos laterales rojos de Material Design
                self.setFillColor("#b91c1c")
                self.rect(0, 0, 15, 792, fill=True, stroke=False)
                self.rect(597, 0, 15, 792, fill=True, stroke=False)
                
                # Línea base de separación inferior
                self.setStrokeColor("#ef4444")
                self.setLineWidth(1)
                self.line(36, 45, 576, 45)
                
                # Footer corporativo inmutable
                self.setFont("Helvetica-Bold", 7)
                self.setFillColor("#1e293b")
                self.drawString(36, 32, "EXPEDIENTE DE SOPORTE DE MATERIALIDAD INMUTABLE - SAT ART. 69-B")
                self.drawRightString(576, 32, f"Página {self._pageNumber} de {page_count}")
            super().showPage()
        super().save()


def handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        print("📡 Extrayendo metadatos multi-tenant de Cognito...")
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        tenant_id = authorizer.get('custom:tenant_id')
        bufete_nombre = authorizer.get('custom:company_name', 'EL PRESTADOR JURÍDICO')

        body = json.loads(event.get('body', '{}'))
        rfc_cliente = body.get('rfc')
        nombre_cliente = body.get('nombre')
        objeto_servicio = body.get('objeto_servicio', 'ANÁLISIS DE BENCHMARKING')
        bimestre = int(body.get('bimestre', 1))

        mapa_bimestres = {
            1: {"archivo": "01 Planificación_Estrategica_Enero_Febreo.pdf", "label": "ENERO-FEBRERO 2021", "estrategia": "PLANIFICACIÓN ESTRATÉGICA"},
            2: {"archivo": "02 Análisis_Benchmarking_Competitivo_Marzo_Abril.pdf", "label": "MARZO-ABRIL 2021", "estrategia": "BENCHMARKING COMPETITIVO"},
            3: {"archivo": "03 Análisis_Benchmarking_Competitivo_Mayo_Junio.pdf", "label": "MAYO-JUNIO 2021", "estrategia": "BENCHMARKING COMPETITIVO"},
            4: {"archivo": "04 Análisis_Benchmarking_Competitivo_Julio_Agosto.pdf", "label": "JULIO-AGOSTO 2021", "estrategia": "BENCHMARKING COMPETITIVO"},
            5: {"archivo": "05 Análisis_Benchmarking_Competitivo_Septiembre_Octubre.pdf", "label": "SEPTIEMBRE-OCTUBRE 2021", "estrategia": "BENCHMARKING COMPETITIVO"},
            6: {"archivo": "06 Análisis_Benchmarking_Competitivo_Noviembre_Diciembre.pdf", "label": "NOVIEMBRE-DICIEMBRE 2021", "estrategia": "REPORTE GENERAL COMPARATIVO"}
        }
        
        config = mapa_bimestres.get(bimestre, mapa_bimestres)

        # 🚀 LECTURA SEGURA DESDE DYNAMODB NOSQL
        print("💾 Consultando el documento del expediente en DynamoDB NoSQL...")
        hash_key = f"{tenant_id}#{rfc_cliente.upper().strip()}"
        table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE'))
        
        response_nosql = table.get_item(Key={'tenant_rfc': hash_key})
        expediente_item = response_nosql.get('Item', {})
        
        # Desempaquetamos de forma segura el arreglo NoSQL
        lista_productos_nosql = expediente_item.get('catalogo_benchmarking', [])
        layout_variable = expediente_item.get('layout_nosql', {})
        
        tesis_fiscal = layout_variable.get('estrategia_pericial', config['estrategia'])
        justificacion_sat = layout_variable.get('justificacion_sat_fase2', 'Soporte documental del Art. 69-B')

        string_catalogo_ia = ""
        catalogo_para_reportlab = []

        # Escudo de paracaídas contra contaminación o datos ausentes
        if isinstance(lista_productos_nosql, list) and len(lista_productos_nosql) > 0:
            for prod in lista_productos_nosql:
                amplitud = prod.get('amplitud_linea', 'Concepto General')
                profundidad = prod.get('profundidad_presentacion', 'U.M.')
                precio = prod.get('precio_lista', 0.00)
                
                string_catalogo_ia += f"- {amplitud} ({profundidad}) con precio de lista de ${float(precio):,.2f} MXN\n"
                catalogo_para_reportlab.append((f"{amplitud} {profundidad}", float(precio)))
        else:
            string_catalogo_ia = "- Servicios Especializados de Consultoría Corporativa y Análisis de Mercado Variable\n"
            catalogo_para_reportlab.append(("Servicios Especializados de Consultoría Corporativa", 1609562.93))

        # 🧠 PROMPT DINÁMICO ADAPTATIVO ASIMILADO POR CLAUDE 4.5
        print("🧠 Invocando a Claude 4.5 Haiku en Amazon Bedrock...")
        prompt_libro = f"""
        Humano: Actúa como Perito Senior en Auditoría Fiscal y Compliance en México. Redacta el cuerpo pericial de un libro corporativo pericial para el periodo: "{config['label']}" bajo la tesis de: "{tesis_fiscal}".

        EL CASO BAJO AUDITORÍA:
        - Cliente: {nombre_cliente.upper()} (RFC: {rfc_cliente}).
        - Consultor: {bufete_nombre.upper()}.
        - Objeto del Instrumento: "{objeto_servicio}".
        - Justificación ante Autoridades (SAT): "{justificacion_sat}".

        REQUISITOS DE CONTENIDO:
        Genera de forma exhaustiva tres secciones: INTRODUCCIÓN, PRESENTACIÓN y JUSTIFICACIÓN. Vincula los argumentos con el portafolio inmutable de soluciones capturadas por el despacho:
        {string_catalogo_ia}

        REGLA ESTRICTA DE FORMATO: No incluyas notas de autor, comentarios de cortesía, ni utilices caracteres Markdown de software como almohadillas (#) o asteriscos (*). Usa texto formal plano y limpio. Comienza directamente con los párrafos.
        Asistente:
        """

        body_payload = json.dumps({
            "anthropic_version": "bedrock-2023-05-31", 
            "max_tokens": 2000, 
            "temperature": 0.1,
            "messages": [{"role": "user", "content": prompt_libro}]
        })

        response = bedrock_runtime.invoke_model(
            body=body_payload, 
            modelId="us.anthropic.claude-haiku-4-5-20251001-v1:0", 
            accept="application/json", 
            contentType="application/json"
        )
        texto_pericial = json.loads(response.get('body').read()).get('content', [{}])[0].get('text', '')

        # COMPILACIÓN EDITORIAL DE ALTA FIDELIDAD (ReportLab)
        print("🎨 Ensamblando el documento PDF en la memoria RAM...")
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer, 
            pagesize=letter, 
            rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
        )
        styles = getSampleStyleSheet()
        
        style_cover_title = ParagraphStyle('CoverT', fontName='Helvetica-Bold', fontSize=22, leading=28, textColor='#0f172a', alignment=TA_CENTER)
        style_cover_sub = ParagraphStyle('CoverS', fontName='Helvetica-Bold', fontSize=16, leading=22, textColor='#b91c1c', alignment=TA_CENTER)
        style_meta_label = ParagraphStyle('MetaL', fontName='Helvetica', fontSize=9, leading=13, textColor='#475569', alignment=TA_CENTER)
        
        style_h1 = ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=13, leading=16, textColor='#0f172a', spaceBefore=14, spaceAfter=8)
        style_body_legal = ParagraphStyle('BL', fontName='Helvetica', fontSize=10, leading=15, textColor='#334155', alignment=TA_JUSTIFY, spaceAfter=8)
        style_cell_th = ParagraphStyle('CTH', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor='#ffffff', alignment=TA_CENTER)
        style_cell_td = ParagraphStyle('CTD', fontName='Helvetica', fontSize=9, leading=11, textColor='#1e293b')

        story = []

        # PORTADA (Page 1)
        story.append(Spacer(1, 40))
        story.append(Paragraph("ANÁLISIS DE BENCHMARKING", style_cover_title))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"{tesis_fiscal.upper()}", style_cover_sub))
        story.append(Spacer(1, 15))
        story.append(Paragraph(f"PERÍODO: {config['label']}", style_cover_title))
        story.append(Spacer(1, 220))
        story.append(Paragraph(f"CLIENTE: {nombre_cliente.upper()}", style_meta_label))
        story.append(Spacer(1, 15))
        story.append(Paragraph(f"EMPRESA: {bufete_nombre.upper()}", style_meta_label))
        story.append(PageBreak())

        meta_table_data = [
            [Paragraph("SERVICIO: ANÁLISIS DE BENCHMARKING", style_cell_th), Paragraph(f"FOLIO: {200 + bimestre}", style_cell_th)],
            [Paragraph(f"ESTRATEGIA: {config['estrategia']}", style_cell_th), Paragraph(f"FECHA: {config['label']}", style_cell_th)]
        ]
        meta_table = Table(meta_table_data, colWidths=[250, 254])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#991b1b')), 
            ('PADDING', (0,0), (-1,-1), 6), 
            ('GRID', (0,0), (-1,-1), 1, colors.white)
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 15))

        for p in texto_pericial.split('\n'):
            clean_p = p.strip()
            if not clean_p: continue
            
            # Limpiamos caracteres residuales de software para que no salgan en el PDF
            clean_p = clean_p.replace('#', '').replace('*', '').strip()
            
            if clean_p.upper().startswith(("INTRODUCCIÓN", "PRESENTACIÓN", "JUSTIFICACIÓN", "CONCLUSIÓN")):
                story.append(Paragraph(clean_p, style_h1))
            else:
                story.append(Paragraph(clean_p, style_body_legal))

        story.append(Spacer(1, 15))
        story.append(Paragraph("10. RELACIÓN DE PRODUCTOS Y VALORES DE MERCADO (BENCHMARKING)", style_h1))
        story.append(Paragraph("A continuación, se plasma la matriz de control del catálogo comercial inmutable extraída del ecosistema NoSQL:", style_body_legal))
        story.append(Spacer(1, 10))

        catalogo_precios_data = [[
            Paragraph("Fotografía Evidencia", style_cell_th),
            Paragraph("Concepto / Solución de Referencia", style_cell_th), 
            Paragraph("Valor Comercial de Lista", style_cell_th)
        ]]
        
        estilos_tabla = [
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1'))
        ]

        for i, (desc_prod, precio_prod, img_obj) in enumerate(catalogo_para_reportlab):
            row_idx = i + 1
            
            # Si el producto no tiene imagen, inyectamos un Paragraph seguro en la celda
            celda_foto = img_obj if img_obj else Paragraph("Sin Evidencia", style_cell_td)
            
            catalogo_precios_data.append([
                celda_foto,
                Paragraph(desc_prod, style_cell_td), 
                Paragraph(f"$ {precio_prod:,.2f} MXN", style_cell_td)
            ])
            bg_color = colors.white if row_idx % 2 != 0 else colors.HexColor('#f8fafc')
            estilos_tabla.append(('BACKGROUND', (0, row_idx), (-1, row_idx), bg_color))

        tabla_precios = Table(catalogo_precios_data, colWidths=[90, 264, 150])
        tabla_precios.setStyle(TableStyle(estilos_tabla))
        story.append(tabla_precios)

        doc.build(story, canvasmaker=CanvasLibroCorporativo)
        pdf_buffer.seek(0)
        pdf_bytes = pdf_buffer.read()
        
        print("Almacenando el PDF resultante en la estructura forense de S3...")
        bucket_name = os.environ.get('BUCKET_NAME')
        s3_key_final = f"{tenant_id}/{rfc_cliente}/1. Análisis Benchmarking Competitivo/02 Materialidad/{config['archivo']}"
        s3_client.put_object(Bucket=bucket_name, Key=s3_key_final, Body=pdf_bytes, ContentType='application/pdf')

        url_firmada = s3_client.generate_presigned_url(
            ClientMethod='get_object', 
            Params={'Bucket': bucket_name, 'Key': s3_key_final}, 
            ExpiresIn=1800
        )

        print("Actualizando el estatus del expediente en la base NoSQL...")
        table.update_item(
            Key={'tenant_rfc': hash_key},
            UpdateExpression=f"SET archivos.materialidad_b{bimestre} = :b",
            ExpressionAttributeValues={':b': {"status": "COMPLETO", "s3_key": s3_key_final, "download_url": url_firmada, "updated_at": datetime.utcnow().isoformat() + "Z"}}
        )

        return {
            'statusCode': 200, 
            'headers': headers, 
            'body': json.dumps({'success': True, 'download_url': url_firmada, 'bimestre': bimestre})
        }
    except Exception as e:
        print(f"❌ Error crítico en bitácora NoSQL bimestral: {str(e)}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}