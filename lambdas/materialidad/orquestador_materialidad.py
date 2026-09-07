import os
import json
import boto3
from datetime import datetime

ssm_client = boto3.client('ssm')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

_CACHED_DB_HOST = None

def obtener_endpoint_db_dinamico():
    """
    Se conecta con AWS SSM Parameter Store para resolver la ruta inyectada
    por los Globas de CloudFormation de forma segura en tiempo de ejecución.
    """
    global _CACHED_DB_HOST
    if _CACHED_DB_HOST:
        return _CACHED_DB_HOST
        
    # Recuperamos la ruta del parámetro del mapa Globals de tu template.yml
    param_path_host = os.environ.get('DB_HOST_PARAM')
    print(f"📡 Solicitando aduana de red a SSM para la ruta: {param_path_host}")
    
    try:
        response = ssm_client.get_parameter(Name=param_path_host, WithDecryption=False)
        _CACHED_DB_HOST = response['Parameter']['Value'].strip()
        return _CACHED_DB_HOST
    except Exception as e:
        print(f"❌ Error crítico al resolver DB_HOST_PARAM en SSM: {str(e)}")
        raise e

def handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    if event.get('httpMethod') == 'OPTIONS': 
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        print("📡 Extrayendo claims multi-tenant y token de Cognito...")
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        tenant_id = authorizer.get('custom:tenant_id')

        # 🚀 SOLUCIÓN REINA: Resolvemos el host dinámico de tu database-infra antes de operar
        db_host_real = obtener_endpoint_db_dinamico()
        print(f"🎯 Conexión exitosa a la infraestructura de red en: {db_host_real}")

        body = json.loads(event.get('body', '{}'))
        flujo = body.get('flujo', 'PREVENTIVO').upper().strip() # PREVENTIVO o RECONSTRUCTIVO
        rfc_cliente = body.get('rfc', '').upper().strip()
        nombre_cliente = body.get('nombre', '')
        ano_fiscal = str(body.get('ano_fiscal', '2026'))
        
        # Lista de contratos variables detectados semánticamente o elegidos en el formulario
        contratos_a_generar = body.get('contratos', ['PRESTACION_SERVICIOS']) 

        # Recuperamos la tabla NoSQL (Asegúrate de tener la variable DYNAMODB_TABLE mapeada o resuelta)
        # Nota: Si tu tabla dynamo también muta por parámetro, puedes llamarla con ssm_client de la misma forma
        nombre_tabla_dynamo = os.environ.get('DYNAMODB_TABLE', f'veritas-control-materialidad-status-{os.environ.get("Environment", "dev")}')
        table = dynamodb.Table(nombre_tabla_dynamo)
        
        for contrato in contratos_a_generar:
            hash_key = f"{tenant_id}#{rfc_cliente}#{contrato}#{ano_fiscal}"
            
            table.put_item(
                Item={
                    'tenant_rfc_year_contract': hash_key,
                    'rfc_cliente': rfc_cliente,
                    'nombre_cliente': nombre_cliente,
                    'ano_fiscal': ano_fiscal,
                    'contrato_tipo': contrato,
                    'tipo_flujo': flujo,
                    'progreso_porcentaje': 10,
                    'estatus_global': 'PROCESANDO',
                    'creado_el': datetime.utcnow().isoformat() + "Z",
                    'archivos': {}
                }
            )

        payload_asincrono = {
            "tenant_id": tenant_id,
            "rfc_cliente": rfc_cliente,
            "nombre_cliente": nombre_cliente,
            "ano_fiscal": ano_fiscal,
            "contratos": contratos_a_generar,
            "tipo_flujo": flujo
        }
        
        lambda_client.invoke(
            FunctionName=os.environ.get('WORKER_LAMBDA_NAME'),
            InvocationType='Event',
            Payload=json.dumps(payload_asincrono)
        )

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': f'Pipeline iniciado con éxito. Se están procesando {len(contratos_a_generar)} expedientes en segundo plano.',
                'expedientes_creados': contratos_a_generar
            })
        }
    except Exception as e:
        print(f"❌ Error en orquestador central: {str(e)}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
