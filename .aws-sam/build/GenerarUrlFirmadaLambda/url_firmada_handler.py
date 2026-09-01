import os
import json
import uuid
import boto3
from botocore.config import Config

# Forzamos el uso de firmas V4 criptográficas para evitar problemas de red regional
s3_client = boto3.client('s3', region_name='us-east-1', config=Config(signature_version='s3v4'))

def handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }

    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        tenant_id = authorizer.get('custom:tenant_id')
        
        # Obtenemos la extensión que React solicita (csv o xlsx)
        params = event.get('queryStringParameters', {}) or {}
        ext = params.get('ext', 'csv').replace('.', '')
        
        # Fabricamos una llave de almacenamiento única estructurada
        # Ej: "bufete-123/facturas_sat_78abcd.csv"
        bucket_name = os.environ.get('BUCKET_NAME')
        object_key = f"{tenant_id}/reporte_sat_{uuid.uuid4().hex[:8]}.{ext}"

        print(f"🎫 Generando Presigned URL para el bucket {bucket_name} e hilos: {object_key}")

        # Generamos el pase de abordaje para S3 de tipo PutObject
        url_firmada = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_key,
                'ContentType': 'application/octet-stream',
                # Grabamos de forma inmutable el tenant_id dentro del archivo en S3
                'Metadata': {'tenant-id': tenant_id}
            },
            ExpiresIn=300 # Expiración estricta de 5 minutos
        )

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'upload_url': url_firmada,
                'object_key': object_key
            })
        }
    except Exception as e:
        print(f"🛑 Error fabricando link de S3: {str(e)}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
