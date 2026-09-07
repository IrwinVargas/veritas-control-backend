import os
import json
import io
import zipfile
import boto3
from datetime import datetime

s3_client = boto3.client('s3')

def handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    if event.get('httpMethod') == 'OPTIONS': 
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        print("🗜️ Inicializando empaquetador compresor de expedientes ZIP...")
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        tenant_id = authorizer.get('custom:tenant_id', 'bufete-veritas')

        body = json.loads(event.get('body', '{}'))
        rfc_cliente = body.get('rfc', '').upper().strip()
        ano_fiscal = str(body.get('ano_fiscal', '2026'))

        if not rfc_cliente:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'RFC del cliente requerido.'})}

        bucket_name = os.environ.get('BUCKET_NAME')
        
        # 📂 Prefijo virtual de S3 que delimita el año completo de este cliente
        s3_prefix_target = f"{tenant_id}/{rfc_cliente}/{ano_fiscal}/"
        print(f"🪣 Escaneando el búnker de S3 en la ruta: {s3_prefix_target}")

        # Listamos todos los PDFs creados asíncronamente por el pipeline en ese año
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix=s3_prefix_target)

        # Inicializamos el buffer de compresión directa en la memoria RAM de la Lambda
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            conteo_archivos = 0
            
            for page in pages:
                for obj in page.get('Contents', []):
                    s3_key = obj['Key']
                    if s3_key.endswith('/'): continue # Saltamos directorios vacíos

                    # Descargamos los bytes del PDF de forma interna ultra-veloz
                    obj_bytes = s3_client.get_object(Bucket=bucket_name, Key=s3_key)['Body'].read()
                    
                    # 🚀 CONSERVACIÓN DE TU LAYOUT: 
                    # Removemos el prefijo del tenant y el RFC para que al abrir el ZIP en la Mac,
                    # el abogado vea directamente las carpetas limpias del SAT: "0. Contrato/", "1. Análisis..."
                    relative_path_zip = s3_key.replace(s3_prefix_target, "")
                    
                    # Inyectamos el archivo al ZIP en caliente
                    zip_file.writestr(relative_path_zip, obj_bytes)
                    conteo_archivos += 1

            if conteo_archivos == 0:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': f'No se encontraron documentos completados para el ejercicio {ano_fiscal}. Genere la materialidad primero.'})
                }

        # Posicionamos el puntero al inicio del buffer binario resultante
        zip_buffer.seek(0)
        zip_bytes = zip_buffer.read()

        # Depositamos el archivo .ZIP final compactado en un nido temporal de S3
        s3_key_zip_final = f"exports/{tenant_id}_{rfc_cliente}_{ano_fiscal}_EXPEDIENTE_SAT.zip"
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key_zip_final,
            Body=zip_bytes,
            ContentType='application/zip'
        )

        # Sello digital: Firmamos la Presigned URL de descarga directa de S3 por 15 minutos
        url_descarga_zip = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': bucket_name, 'Key': s3_key_zip_final},
            ExpiresIn=900
        )

        print(f"🎯 ZIP Forense compilado exitosamente. {conteo_archivos} PDFs empaquetados.")
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'download_url': url_descarga_zip,
                'total_archivos': conteo_archivos
            })
        }
    except Exception as e:
        print(f"❌ Crash en empaquetador ZIP: {str(e)}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
