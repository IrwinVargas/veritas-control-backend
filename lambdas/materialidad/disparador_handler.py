# =========================================================================
# PUENTE GATILLO FINAL: CONEXIÓN REAL CON LLAVE DE PARTICIÓN COMPUESTA
# RUTA EN MAC: lambdas/materialidad/disparador_handler.py
# =========================================================================
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
        # 🔐 Extracción segura del tenant_id real desde las claims criptográficas de Cognito
        request_context = event.get('requestContext', {}) if isinstance(event, dict) else {}
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        tenant_id = claims.get('custom:tenant_id') or claims.get('custom:tenantId') or claims.get('tenant_id')
        
        # Destapamos el payload enviado por React desde la aduana Proxy
        body_crudo = event.get('body') if isinstance(event, dict) else None
        if body_crudo:
            payload = json.loads(body_crudo) if isinstance(body_crudo, str) else body_crudo
        else:
            payload = json.loads(event) if isinstance(event, str) else event

        if not isinstance(payload, dict):
            payload = {}

        # Mapeamos los datos de la empresa cliente (Receptor)
        rfc_cliente = payload.get('rfc_cliente') or payload.get('rfcCliente')
        nombre_cliente = payload.get('nombre_cliente') or payload.get('nombreCliente', 'Contribuyente Auditado')
        contrato = payload.get('contrato') or 'PRESTACION_SERVICIOS'
        ano_fiscal = payload.get('ano_fiscal') or str(datetime.now().year)
        tipo_flujo = payload.get('tipo_flujo') or 'RECONSTRUCTIVO'

        if not tenant_id or not rfc_cliente:
            print("❌ Error de validación: Parámetros nulos en el authorizer o payload.")
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Faltan parámetros críticos de identidad para armar las llaves de AWS'})
            }

        # =========================================================================
        # 🚀 REPARACIÓN REINA DYNAMODB: FUSIÓN DE LLAVE COMPUESTA 'tenant_rfc'
        # Armamos de forma simétrica el string concatenado rígido exigido por tu esquema NoSQL
        # =========================================================================
        llave_compuesta_nosql = f"{str(tenant_id).strip()}#{str(rfc_cliente).strip()}"
        print(f"🔎 Llave Maestra NoSQL Consolidada: [{llave_compuesta_nosql}]")

        nombre_tabla = os.environ.get('NOTIFICACIONES_TABLE') or os.environ.get('DYNAMODB_TABLE') or "veritas-control-materialidad-nosql-dev"
        table = dynamodb.Table(nombre_tabla)
        
        fecha_actual_unix = int(datetime.utcnow().timestamp())
        ttl_10_dias = fecha_actual_unix + (10 * 24 * 60 * 60)

        print(f"💾 Inyectando de forma física la tupla fundadora en DynamoDB...")
        table.put_item(
            Item={
                'tenant_rfc': llave_compuesta_nosql, # 🎯 LLAVE PRIMARIA EXIGIDA POR TU ESQUEMA (Sacia la Validación)
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
            "ano_fiscal": rano_fiscal,
            "tipo_flujo": tipo_flujo,
            "tenant_rfc": llave_compuesta_nosql # Se la pasamos para que los Pasos 1, 2 y 3 hagan sus updates limpiamente
        }

        print(f"🔥 Gatillando Step Function de Materialidad Saneada: {nombre_ejecucion}")
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
                'message': 'Pipeline forense de materialidad encendido de forma 100% real.'
            })
        }

    except Exception as e:
        print(f"❌ Error fatal en el disparador intermedio original: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
