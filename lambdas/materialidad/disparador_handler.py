# =========================================================================
# PUENTE GATILLO: DISPARADOR ASÍNCRONO DE LA STEP FUNCTION DESDE REAT
# RUTA EN MAC: lambdas/materialidad/disparador_handler.py
# =========================================================================
import os
import json
import boto3
from datetime import datetime

# Inicializamos el cliente de AWS Step Functions (States)
states_client = boto3.client('stepfunctions')

def handler(event, context):
    print("📡 Disparador de Materialidad Veritas Activado desde la API Gateway...")
    
    # Manejo de aduanas CORS obligatorias para que React no bloquee la petición
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'CORS OK'})}

    try:
        # Extraemos el payload que envió tu función dispararOrquestadorForense de React
        body = json.loads(event.get('body', '{}')) if event.get('body') else event
        tenant_id = body.get('tenant_id')
        rfc_cliente = body.get('rfc_cliente')
        nombre_cliente = body.get('nombre_cliente')
        contrato = body.get('contrato', 'PRESTACION_SERVICIOS')
        ano_fiscal = body.get('ano_fiscal', str(datetime.now().year))

        if not tenant_id or not rfc_cliente:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Faltan parámetros críticos (tenant_id, rfc_cliente)'})
            }

        # 🚀 LA REFERENCIA DE INFRAESTRUCTURA: Succionamos el ARN real de la Step Function
        # que CloudFormation le inyectó de forma automatizada a esta Lambda
        state_machine_arn = os.environ.get('STATE_MACHINE_ARN')
        
        # Fundamos un nombre de ejecución único cronológico para evitar colisiones en AWS
        nombre_ejecucion = f"EXEC-{rfc_cliente}-{contrato}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Enlazamos el payload exacto que consumirán consecutivamente el Paso 1, Paso 2 y Paso 3
        input_payload = {
            "tenant_id": tenant_id,
            "rfc_cliente": rfc_cliente,
            "nombre_cliente": nombre_cliente,
            "contrato": contrato,
            "ano_fiscal": ano_fiscal,
            "tipo_flujo": "RECONSTRUCTIVO" # Detona tu código de extracción relacional de Postgres
        }

        print(f"🔥 Gatillando Step Function de Materialidad de forma asíncrona: {nombre_ejecucion}")
        
        # Despertamos la Máquina de Estados en 1.5ms
        response = states_client.start_execution(
            stateMachineArn=state_machine_arn,
            name=nombre_ejecucion,
            input=json.dumps(input_payload)
        )

        return {
            'statusCode': 202, # 202 Accepted: Estándar Enterprise de Arquitecturas Orientadas a Eventos
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'execution_arn': response['executionArn'],
                'message': 'Pipeline forense de materialidad encendido en segundo plano con éxito.'
            })
        }

    except Exception as e:
        print(f"❌ Error fatal en el disparador intermedio: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
