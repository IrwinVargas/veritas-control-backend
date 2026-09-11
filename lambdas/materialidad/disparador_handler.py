import os
import json
import boto3
import uuid
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
        # 🚀 REPARACIÓN REINA SÉNIOR: EXTRACTOR PROXY INDESTRUCTIBLE
        # Si viene a través de API Gateway Proxy, succiona de 'body'. Si viene de un test directo, toma el event.
        body_crudo = event.get('body') if isinstance(event, dict) else None
        
        if body_crudo:
            # Si el body de la aduana de AWS viaja como string plano, lo destapamos
            payload = json.loads(body_crudo) if isinstance(body_crudo, str) else body_crudo
        else:
            # Fallback elástico: Si se detonó por consola o Step Functions directo
            payload = json.loads(event) if isinstance(event, str) else event

        # Si por alguna fluctuación el payload sigue envuelto de forma incorrecta, forzamos un diccionario
        if not isinstance(payload, dict):
            payload = {}

        # 📐 SUCCIÓN ATÓMICA DE VARIABLES REALES DE REACT
        tenant_id = payload.get('tenant_id')
        rfc_cliente = payload.get('rfc_cliente')
        nombre_cliente = payload.get('nombre_cliente', 'Contribuyente Auditado')
        contrato = payload.get('contrato', 'PRESTACION_SERVICIOS')
        ano_fiscal = payload.get('ano_fiscal', str(datetime.now().year))
        tipo_flujo = payload.get('tipo_flujo', 'RECONSTRUCTIVO')

        print(f"🔎 Aduana de Sincronización Real: tenant_id=[{tenant_id}], rfc_cliente=[{rfc_cliente}], contrato=[{contrato}]")

        if not tenant_id or not rfc_cliente:
            print("❌ Crash de validación: Parámetros nulos detectados en el dual-parsing.")
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Faltan parámetros críticos (tenant_id, rfc_cliente)',
                    'debug_received_event_keys': list(event.keys()) if isinstance(event, dict) else 'Not a dict'
                })
            }

        # =========================================================================
        # 🚀 PASO 1: FUNDACIÓN FÍSICA INMEDIATA EN DYNAMODB NoSQL
        # =========================================================================
        nombre_tabla = os.environ.get('NOTIFICACIONES_TABLE') or os.environ.get('DYNAMODB_TABLE') or "veritas-control-materialidad-nosql-dev"
        table = dynamodb.Table(nombre_tabla)
        
        fecha_actual_unix = int(datetime.utcnow().timestamp())
        ttl_10_dias = fecha_actual_unix + (10 * 24 * 60 * 60)

        print(f"💾 Sembrando registro Multi-Tenant en DynamoDB para {rfc_cliente} al 25%...")
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

        # =========================================================================
        # 🚀 PASO 2: DISPARO SEGURO DE LA STATE MACHINE (MÁXIMA RESILIENCIA)
        # =========================================================================
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
                'message': 'Pipeline forense de materialidad encendido con éxito.'
            })
        }

    except Exception as e:
        print(f"❌ Error fatal en el disparador intermedio original: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
