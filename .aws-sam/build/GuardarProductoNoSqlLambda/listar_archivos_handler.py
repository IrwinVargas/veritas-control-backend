# backend/lambdas/materialidad/listar_archivos_handler.py
import os
import json
import boto3

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3', region_name='us-east-1')

def handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }

    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        print("📡 Consultando estatus documental en DynamoDB NoSQL...")
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        tenant_id = authorizer.get('custom:tenant_id')

        query_params = event.get('queryStringParameters', {}) or {}
        rfc_cliente = query_params.get('rfc')

        if not tenant_id or not rfc_cliente:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'Parámetros multi-tenant incompletos.'})}

        hash_key = f"{tenant_id}#{rfc_cliente.upper().strip()}"

        nombre_tabla = os.environ.get('DYNAMODB_TABLE')
        table = dynamodb.Table(nombre_tabla)
        
        response = table.get_item(Key={'tenant_rfc': hash_key})
        item = response.get('Item', {})

        if not item:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'success': True,
                    'estatus_expediente': 'PENDIENTE',
                    'archivos': {}
                })
            }

        archivos_documental = item.get('archivos', {})
        bucket_name = os.environ.get('BUCKET_NAME')

        for clave_doc, metadata_doc in archivos_documental.items():
            if metadata_doc.get('status') == 'COMPLETO' and metadata_doc.get('s3_key'):
                try:
                    url_firmada = s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': bucket_name, 'Key': metadata_doc['s3_key']},
                        ExpiresIn=900
                    )
                    metadata_doc['download_url'] = url_firmada
                except Exception as s3_err:
                    print(f"⚠️ Error generando URL firmada para {clave_doc}: {str(s3_err)}")
                    metadata_doc['download_url'] = None

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'estatus_expediente': item.get('estatus_expediente', 'PROCESANDO'),
                'archivos': archivos_documental
            })
        }
    except Exception as e:
        print(f"❌ Error en microservicio lector de archivos materialidad: {str(e)}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
