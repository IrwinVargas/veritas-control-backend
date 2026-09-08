import os
import json
import io
import zipfile
import boto3
from datetime import datetime

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    print("📦 Inicializando empaquetador pericial core_zip_packer_handler...")
    
    # Manejo de aduanas CORS para API Gateway
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        body = json.loads(event.get('body', '{}')) if event.get('body') else event
        tenant_id = body.get('tenant_id')
        rfc_cliente = body.get('rfc_cliente')
        ano_fiscal = body.get('ano_fiscal', str(datetime.now().year))
        contrato = body.get('contrato', 'PRESTACION_SERVICIOS')

        # 🚀 OPCIÓN B LIMPIA: Jalamos el bucket dinámico inyectado por CloudFormation
        bucket_name = os.environ.get('BUCKET_NAME')
        
        # Prefijo raíz del expediente forense dentro de S3
        prefix_raiz = f"{tenant_id}/{rfc_cliente}/{ano_fiscal}/{contrato}/"
        print(f"🔎 Escaneando prefijos virtuales en S3: {bucket_name}/{prefix_raiz}")

        # Listamos todos los insumos (PDFs, XMLs, fotos) depositados por los pasos previos
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix_raiz)

        # Compilación binaria directa en memoria RAM
        zip_buffer = io.BytesIO()
        # Creamos el archivo comprimido en caliente
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            archivos_encontrados = 0
            
            for page in pages:
                for obj in page.get('Contents', []):
                    s3_key = obj['Key']
                    if s3_key.endswith('/'): # Ignoramos carpetas virtuales vacías
                        continue
                    
                    archivos_encontrados += 1
                    print(f"📥 Descargando insumo para empaquetar: {s3_key}")
                    obj_bytes = s3_client.get_object(Bucket=bucket_name, Key=s3_key)['Body'].read()
                    
                    # 📐 MAPEO MAPA INTELECTUAL: Traducimos las rutas de S3 a la fisonomía estricta anti-SAT
                    # Re-acomodamos los bytes dinámicamente según el tipo de documento detectado
                    nombre_archivo = os.path.basename(s3_key)
                    ruta_dentro_del_zip = f"EXPEDIENTE_DIGITAL_{rfc_cliente}/03_EVIDENCIA_MATERIALIDAD/Entregables_y_Reportes/{nombre_archivo}"
                    
                    if "01 Legal" in s3_key or "Contrato" in nombre_archivo:
                        ruta_dentro_del_zip = f"EXPEDIENTE_DIGITAL_{rfc_cliente}/01_LEGAL_Y_CONSTITUTIVO/{nombre_archivo}"
                    elif "02 Cumplimiento" in s3_key or "Opinion" in nombre_archivo or "Constancia" in nombre_archivo:
                        ruta_dentro_del_zip = f"EXPEDIENTE_DIGITAL_{rfc_cliente}/02_CUMPLIMIENTO_FISCAL/{nombre_archivo}"
                    elif "Evidencia_Fotografica" in s3_key or "foto" in nombre_archivo.lower() or "mail" in nombre_archivo.lower():
                        ruta_dentro_del_zip = f"EXPEDIENTE_DIGITAL_{rfc_cliente}/03_EVIDENCIA_MATERIALIDAD/Evidencia_Fotografica_y_Digital/{nombre_archivo}"
                    elif "04 Comprobacion" in s3_key or nombre_archivo.endswith('.xml') or "Factura" in nombre_archivo:
                        ruta_dentro_del_zip = f"EXPEDIENTE_DIGITAL_{rfc_cliente}/04_COMPROBACION_FINANCIERA/{nombre_archivo}"

                    # Inyectamos el archivo en la estructura pericial correspondiente
                    zip_file.writestr(ruta_dentro_del_zip, obj_bytes)

            # Si el expediente está vacío, metemos un README de cortesía para no romper el zip
            if archivos_encontrados == 0:
                zip_file.writestr(f"EXPEDIENTE_DIGITAL_{rfc_cliente}/README.txt", b"Inicializando búnker de materialidad Veritas Control.")

        # Volcamos el ZIP final consolidado a S3
        zip_buffer.seek(0)
        zip_key_final = f"{tenant_id}/{rfc_cliente}/{ano_fiscal}/{contrato}/Expediente_Forense_Consolidado.zip"
        
        print(f"💾 Guardando ZIP definitivo en S3: {zip_key_final}")
        s3_client.put_object(
            Bucket=bucket_name,
            Key=zip_key_final,
            Body=zip_buffer.getvalue(),
            ContentType='application/zip'
        )

        # Generamos el pase de abordaje seguro para descarga directa en React (Vence en 30 minutos)
        url_descarga = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': bucket_name, 'Key': zip_key_final},
            ExpiresIn=1800
        )

        # Actualizamos la tabla NoSQL indicando que el paquete estructural está listo
        table_name = os.environ.get('DYNAMODB_TABLE', f"veritas-control-materialidad-status-{tenant_id}")
        table = dynamodb.Table(table_name)
        hash_key = f"{tenant_id}#{rfc_cliente}#{contrato}#{ano_fiscal}"
        
        table.update_item(
            Key={'tenant_rfc': hash_key},
            UpdateExpression="SET archivos.zip_consolidado = :zip_obj, mensaje_progreso = :m",
            ExpressionAttributeValues={
                ':zip_obj': {"status": "LISTO", "s3_key": zip_key_final, "download_url": url_descarga, "packaged_at": datetime.utcnow().isoformat() + "Z"},
                ':m': "¡Búnker Forense comprimido bajo la estructura estricta del SAT exitosamente!"
            }
        )

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'success': True, 'download_url': url_descarga, 'archivos_empaquetados': archivos_encontrados})
        }
    except Exception as e:
        print(f"❌ Error crítico en core_zip_packer_handler: {str(e)}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}