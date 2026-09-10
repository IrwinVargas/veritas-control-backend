# =========================================================================
# PUENTE GATILLO INMUNE A BLOQUEOS 400: DUAL-PARSING EN PAYLOAD DE RED
# RUTA EN MAC: lambdas/materialidad/disparador_handler.py
# =========================================================================
import os
import json
import boto3
from datetime import datetime

states_client = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    print("📡 Disparador de Materialidad Veritas Activado desde la API Gateway...")
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'CORS OK'})}

    try:
        # 🚀 REPARACIÓN REINA: DUAL-PARSING TOLERANTE A PROXIES DE RED
        # Evaluamos de forma elástica si el JSON viene envuelto por API Gateway o viaja directo en el event
        body = {}
        if isinstance(event, dict):
            if event.get('body'):
                try:
                    body = json.loads(event['body'])
                except:
                    body = event
            else:
                body = event
        elif isinstance(event, str):
            body = json.loads(event)

        # Succión segura con fallbacks de contingencia
        tenant_id = body.get('tenant_id') or event.get('tenant_id')
        rfc_cliente = body.get('rfc_cliente') or event.get('rfc_cliente')
        nombre_cliente = body.get('nombre_cliente') or event.get('nombre_cliente', 'Contribuyente Auditado')
        contrato = body.get('contrato') or event.get('contrato', 'PRESTACION_SERVICIOS')
        ano_fiscal = body.get('ano_fiscal') or event.get('ano_fiscal', str(datetime.now().year))
        tipo_flujo = body.get('tipo_flujo') or event.get('tipo_flujo', 'RECONSTRUCTIVO')

        print(f"🔎 Aduana de Variables: tenant_id=[{tenant_id}], rfc_cliente=[{rfc_cliente}], contrato=[{contrato}]")

        if not tenant_id or not rfc_cliente:
            print("❌ Crash de validación: Parámetros nulos detectados en el dual-parsing.")
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Faltan parámetros críticos (tenant_id, rfc_cliente)',
                    'debug_received_body': str(body)[:200]
                })
            }

        # 🚀 PASO 1: SEMBRADO EN DYNAMODB NoSQL
        nombre_tabla = os.environ.get('NOTIFICACIONES_TABLE') or os.environ.get('DYNAMODB_TABLE') or "veritas-control-materialidad-nosql-dev"
        table = dynamodb.Table(nombre_tabla)
        
        fecha_actual_unix = int(datetime.utcnow().timestamp())
        ttl_10_dias = fecha_actual_unix + (10 * 24 * 60 * 60)

        table.put_item(
            Item={
                'tenant_id': str(tenant_id),          
                'rfc_cliente': str(rfc_cliente),      
                'nombre_cliente': str(nombre_cliente),
                'contrato': str(contrato),
                'tipo_flujo': str(tipo_flujo),
                'estatus_global': 'PROCESANDO',       
                'porcentaje_avance': 25,              
                'fecha_expiracion': ttl_10_dias
            }
        )

        # 🚀 PASO 2: DISPARO DE LA STEP FUNCTION (SANEADO DE CARACTERES)
        state_machine_arn = os.environ.get('STATE_MACHINE_ARN') or os.environ.get('MATERIALIDAD_STATE_MACHINE_ARN')
        
        contrato_saneado = str(contrato).replace('_', '-')
        rfc_saneado = str(rfc_cliente).replace('_', '-')
        timestamp_saneado = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        nombre_ejecucion = f"EXEC-{rfc_saneado}-{contrato_saneado}-{timestamp_saneado}"
        nombre_ejecucion = nombre_ejecucion[:75].upper()
        
        input_payload = {
            "tenant_id": tenant_id,
            "rfc_cliente": rfc_cliente,
            "nombre_cliente": nombre_cliente,
            "contrato": contrato,
            "ano_fiscal": ano_fiscal,
            "tipo_flujo": tipo_flujo
        }

        print(f"🔥 Gatillando Step Function de Materialidad Saneada de forma asíncrona: {nombre_ejecucion}")
        response = states_client.start_execution(
            stateMachineArn=state_machine_arn,
            name=nombre_ejecucion,
            input=json.dumps(input_payload)
        )

        return {
            'statusCode': 202, 
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'execution_arn': response['executionArn'],
                'message': 'Pipeline forense de materialidad encendido en segundo plano con éxito.'
            })
        }

    except Exception as e:
        print(f"❌ Error fatal en el disparador intermedio original: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
