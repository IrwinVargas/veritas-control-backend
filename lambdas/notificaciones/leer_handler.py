import os
import json
import boto3

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    print("📡 Registrando lectura atómica de notificación en la nube...")
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        tenant_id = authorizer.get('custom:tenant_id', 'bufete-veritas-uuid-1111')

        body = json.loads(event.get('body', '{}'))
        notificacion_id = body.get('notificacion_id')

        if not notificacion_id:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'notificacion_id es requerido'})}

        nombre_tabla = os.environ.get('NOTIFICACIONES_TABLE', 'veritas-control-notificaciones-dev')
        table = dynamodb.Table(nombre_tabla)

        # ⚡ UPDATE ATÓMICO: Modificamos únicamente el casillero leido sin re-escribir todo el JSON
        table.update_item(
            Key={
                'tenant_id': tenant_id,
                'notificacion_id': notificacion_id
            },
            UpdateExpression="SET leido = :l",
            ExpressionAttributeValues={':l': True}
        )

        print(f"🎯 Notificación [{notificacion_id}] firmada como leída de forma exitosa.")
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'success': True})
        }

    except Exception as e:
        print(f"❌ Crash en persistidor de lectura: {str(e)}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
