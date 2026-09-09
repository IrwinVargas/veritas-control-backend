import os
import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    print("📡 Descargando historial de notificaciones real desde el búnker NoSQL...")
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        tenant_id = authorizer.get('custom:tenant_id', 'bufete-veritas-uuid-1111')

        nombre_tabla = os.environ.get('NOTIFICACIONES_TABLE', 'veritas-control-notificaciones-dev')
        table = dynamodb.Table(nombre_tabla)

        response = table.query(
            KeyConditionExpression=Key('tenant_id').eq(tenant_id),
            ScanIndexForward=False, # ⏱️ Orden cronológico inverso: Las más recientes primero estilo Facebook
            Limit=20 # Cap de cortesía para mantener la latencia en 0.1ms
        )

        notificaciones_mapeadas = []
        for item in response.get('Items', []):
            notificaciones_mapeadas.append({
                'id': item.get('notificacion_id'),
                'tipo': item.get('tipo', 'SISTEMA'),
                'titulo': item.get('titulo'),
                'descripcion': item.get('descripcion'),
                'creadoEl': item.get('creado_el'),
                'leido': item.get('leido', False)
            })

        print(f"✅ Descarga completada: {len(notificaciones_mapeadas)} alertas vivas escupidas hacia React.")
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'notificaciones': notificaciones_mapeadas})
        }

    except Exception as e:
        print(f"❌ Crash crítico en historiador NoSQL: {str(e)}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
