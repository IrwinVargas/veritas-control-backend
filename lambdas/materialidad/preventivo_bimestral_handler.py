# =========================================================================
# PUENTE GATILLO ULTRA-SEGURO: EXTRACCIÓN CRIPTOGRÁFICA DESDE COGNITO CLAIMS
# RUTA EN MAC: lambdas/materialidad/disparador_handler.py
# =========================================================================
import os
import json
import boto3
import uuid
from datetime import datetime

# Inicializamos los conectores perimetrales de AWS
states_client = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')

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
        # 🚀 REPARACIÓN REINA 1: EXTRACCIÓN CRIPTOGRÁFICA MULTI-TENANT DESDE EL RECONSTR_CONTEXT
        # Jalamos el identificador del despacho directamente desde las claims de AWS Cognito decodificadas por el Proxy
        request_context = event.get('requestContext', {}) if isinstance(event, dict) else {}
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        
        # Succión elástica del tenant_id desde las tres posibles firmas del token criptográfico de Cognito
        tenant_id = claims.get('custom:tenant_id') or claims.get('custom:tenantId') or claims.get('tenant_id')
        
        # Destapamos el cuerpo interno enviado por React para los datos del cliente
        body_crudo = event.get('body') if isinstance(event, dict) else None
        if body_crudo:
            payload = json.loads(body_crudo) if isinstance(body_crudo, str) else body_crudo
        else:
            payload = json.loads(event) if isinstance(event, str) else event

        if not isinstance(payload, dict):
            payload = {}

        # Mapeamos los datos específicos de la empresa cliente (Receptor del SAT)
        rfc_cliente = payload.get('rfc_cliente') or payload.get('rfcCliente')
        nombre_cliente = payload.get('nombre_cliente') or payload.get('nombreCliente', 'Contribuyente Auditado')
        contrato = payload.get('contrato') or 'PRESTACION_SERVICIOS'
        ano_fiscal = payload.get('ano_fiscal') or str(datetime.now().year)
        tipo_flujo = payload.get('tipo_flujo') or 'RECONSTRUCTIVO'

        # Log pericial con match de red exacto libre de None
        print(f"🔎 Aduana Real Veritas: tenant_id=[{tenant_id}], rfc_cliente=[{rfc_cliente}], contrato=[{contrato}]")

        if not tenant_id or not rfc_cliente:
            print("❌ Error de validación: tenant_id de Cognito o rfc_cliente de React llegaron vacíos.")
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Faltan parámetros críticos de identidad (tenant_id de Cognito o rfc_cliente de React)',
                    'debug_authorizer_keys': list(claims.keys()) if isinstance(claims, dict) else 'No claims available'
                })
            }

        # =========================================================================
        # 🚀 PASO 1: FUNDACIÓN FÍSICA IMPECABLE EN DYNAMODB NoSQL
        # =========================================================================
        nombre_tabla = os.environ.get('NOTIFICACIONES_TABLE') or "veritas-control-materialidad-nosql-dev"
        table = dynamodb.Table(nombre_tabla)
        
        fecha_actual_unix = int(datetime.utcnow().timestamp())
        ttl_10_dias = fecha_actual_unix + (10 * 24 * 60 * 60)

        print(f"💾 Sembrando registro Multi-Tenant en DynamoDB para {rfc_cliente} al 25%...")
        table.put_item(
            Item={
                'tenant_id': str(tenant_id),          # HASH Key Criptográfica Real
                'rfc_cliente': str(rfc_cliente),      # RANGE Key
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
