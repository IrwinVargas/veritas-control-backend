import os
import json
import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }

    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        print("Inicializando inyección de producto flexible en DynamoDB NoSQL...")
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        tenant_id = authorizer.get('custom:tenant_id')

        if not tenant_id:
            return {'statusCode': 401, 'headers': headers, 'body': json.dumps({'error': 'Firma multi-tenant no válida.'})}

        body = json.loads(event.get('body', '{}'))
        rfc_cliente = str(body.get('rfc', '')).strip().upper()
        amplitud = str(body.get('amplitud_linea', '')).strip()
        profundidad = str(body.get('profundidad_presentacion', '')).strip()
        precio = body.get('precio_lista', 0.0)

        if not rfc_cliente or not amplitud or not profundidad:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'Lineamientos del producto incompletos.'})}

        hash_key = f"{tenant_id}#{rfc_cliente}"
        table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE'))
        key_imagen = body.get('key_imagen_s3', '')

        nuevo_producto = {
            "amplitud_linea": amplitud,
            "profundidad_presentacion": profundidad,
            "precio_lista": Decimal(str(precio)),
            "key_imagen_s3": key_imagen,
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }

        print(f"Insertando {amplitud} de forma atómica en el arreglo NoSQL...")
        table.update_item(
            Key={'tenant_rfc': hash_key},
            UpdateExpression="SET catalogo_benchmarking = list_append(if_not_exists(catalogo_benchmarking, :empty_list), :p)",
            ExpressionAttributeValues={
                ':empty_list': [],
                ':p': [nuevo_producto] # Debe pasarse envuelto en una lista para concatenarse
            }
        )

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'success': True, 'message': 'Atributo flexible incorporado al documento NoSQL.'})
        }
    except Exception as e:
        print(f"❌ Error en persistencia NoSQL de productos: {str(e)}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
