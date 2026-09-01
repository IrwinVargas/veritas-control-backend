import os
import json
import boto3

sfn_client = boto3.client('stepfunctions', region_name='us-east-1')

def handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }

    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        print("🚀 Disparando máquina de estados pericial asíncrona...")
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        tenant_id = authorizer.get('custom:tenant_id')

        body = json.loads(event.get('body', '{}'))
        rfc_cliente = body.get('rfc')
        nombre_cliente = body.get('nombre')

        if not tenant_id or not rfc_cliente:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'Parámetros multi-tenant incompletos.'})}

        input_payload = {
            "tenant_id": tenant_id,
            "rfc_cliente": rfc_cliente.upper().strip(),
            "nombre_cliente": nombre_cliente,
            "bucket_destino": os.environ.get('STATE_MACHINE_ARN').split(':')[-2] # Autodetecta el bucket dinámicamente
        }

        sfn_client.start_execution(
            stateMachineArn=os.environ.get('STATE_MACHINE_ARN'),
            input=json.dumps(input_payload)
        )

        print(f"🎯 Orquestador encendido con éxito para el cliente: {rfc_cliente}")
        
        return {
            'statusCode': 202,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': 'El expediente pericial de materialidad está siendo compilado con IA en segundo plano.'
            })
        }
    except Exception as e:
        print(f"❌ Error disparando orquestador: {str(e)}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
