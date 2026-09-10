import os
import json
import uuid
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
sfn_client = boto3.client('stepfunctions', region_name='us-east-1')

def handler(event, context):
    print("📡 Petición /materialidad/detonar recibida de forma perimetral...")
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        body = json.loads(event.get('body', '{}'))
        
        tenant_id = body.get('tenant_id')
        rfc_cliente = body.get('rfc_cliente')
        nombre_cliente = body.get('nombre_cliente', 'Contribuyente Auditado')
        contrato_tipo = body.get('contrato', 'DESARROLLO_TECNOLOGICO')
        tipo_flujo = body.get('tipo_flujo', 'RECONSTRUCTIVO')

        if not tenant_id or not rfc_cliente:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'tenant_id y rfc_cliente son requeridos'})}

        # =========================================================================
        # 🚀 PASO 1: FUNDACIÓN FÍSICA INDESTRUCTIBLE EN DYNAMODB NoSQL
        # Sembramos el registro al 25% de avance para encender la barra en React
        # =========================================================================
        nombre_tabla = os.environ.get('NOTIFICACIONES_TABLE', 'veritas-control-materialidad-nosql-dev')
        table = dynamodb.Table(nombre_tabla)
        
        fecha_actual_unix = int(datetime.utcnow().timestamp())
        ttl_10_dias = fecha_actual_unix + (10 * 24 * 60 * 60) # Candado de borrado automático SAT

        print(f"💾 Fundando registro Multi-Tenant en DynamoDB para {rfc_cliente}...")
        table.put_item(
            Item={
                'tenant_id': str(tenant_id),          # HASH Key
                'rfc_cliente': str(rfc_cliente),      # RANGE Key
                'nombre_cliente': str(nombre_cliente),
                'contrato': str(contrato_tipo),
                'tipo_flujo': str(tipo_flujo),
                'estatus_global': 'PROCESANDO',       # Detona los engranes en el Header
                'porcentaje_avance': 25,              # Inicializa la barra al 25%
                'fecha_expiracion': ttl_10_dias
            }
        )

        # =========================================================================
        # 🚀 PASO 2: DISPARO SEGURO DE LA STATE MACHINE (STEP FUNCTION)
        # =========================================================================
        print("⚡ Registro fundado con éxito. Gatillando la Step Function asíncrona...")
        state_machine_arn = os.environ.get('MATERIALIDAD_STATE_MACHINE_ARN', 'arn:aws:states:us-east-1:049255850526:stateMachine:veritas-control-materialidad-pipeline-dev')
        
        payload_orquestador = {
            "tenant_id": str(tenant_id),
            "rfc_cliente": str(rfc_cliente),
            "nombre_cliente": str(nombre_cliente),
            "ano_fiscal": "2026",
            "contrato": str(contrato_tipo),
            "tipo_flujo": str(tipo_flujo)
        }
        
        sfn_client.start_execution(
            stateMachineArn=state_machine_arn,
            name=f"ORQUESTADOR-{str(tenant_id)[:8].upper()}-{str(uuid.uuid4())[:6].upper()}",
            input=json.dumps(payload_orquestador)
        )

        print("🎯 ¡Circuito cerrado en verde total! Proceso asíncrono marchando.")
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'success': True, 'message': 'Proceso de materialidad iniciado'})
        }

    except Exception as e:
        print(f"❌ Crash crítico en el inicializador perimetral: {str(e)}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
