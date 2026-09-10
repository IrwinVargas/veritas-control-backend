import os
import json
import boto3
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
        # Extraemos el payload que envió tu función dispararOrquestadorForense de React
        body = json.loads(event.get('body', '{}')) if event.get('body') else event
        tenant_id = body.get('tenant_id')
        rfc_cliente = body.get('rfc_cliente')
        nombre_cliente = body.get('nombre_cliente', 'Contribuyente Auditado')
        contrato = body.get('contrato', 'PRESTACION_SERVICIOS')
        ano_fiscal = body.get('ano_fiscal', str(datetime.now().year))
        tipo_flujo = body.get('tipo_flujo', 'RECONSTRUCTIVO')

        if not tenant_id or not rfc_cliente:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Faltan parámetros críticos (tenant_id, rfc_cliente)'})
            }

        # =========================================================================
        # 🚀 INYECCIÓN MAESTRA 1: FUNDACIÓN FÍSICA INMEDIATA EN DYNAMODB NoSQL
        # Sembramos el registro al 25% de avance para encender la barra de carga en React
        # =========================================================================
        nombre_tabla = os.environ.get('NOTIFICACIONES_TABLE') or os.environ.get('DYNAMODB_TABLE')
        if not nombre_tabla:
            # Fallback elástico seguro de infraestructura por entornos
            nombre_tabla = "veritas-control-materialidad-nosql-dev"
            
        table = dynamodb.Table(nombre_tabla)
        
        fecha_actual_unix = int(datetime.utcnow().timestamp())
        ttl_10_dias = fecha_actual_unix + (10 * 24 * 60 * 60)

        print(f"💾 Fundando registro Multi-Tenant en DynamoDB para {rfc_cliente} al 25%...")
        table.put_item(
            Item={
                'tenant_id': str(tenant_id),          # HASH Key
                'rfc_cliente': str(rfc_cliente),      # RANGE Key
                'nombre_cliente': str(nombre_cliente),
                'contrato': str(contrato),
                'tipo_flujo': str(tipo_flujo),
                'estatus_global': 'PROCESANDO',       # Enciende los engranes en React
                'porcentaje_avance': 25,              # Inicializa la barra al 25%
                'fecha_expiracion': ttl_10_dias
            }
        )

        # =========================================================================
        # 🚀 INYECCIÓN MAESTRA 2: DISPARO DE LA STATE MACHINE (MÁXIMA RESILIENCIA)
        # Saneamos de forma quirúrgica los guiones bajos prohibidos del execution name
        # para destruir el crash de validación de la API nativa de AWS Step Functions
        # =========================================================================
        state_machine_arn = os.environ.get('STATE_MACHINE_ARN') or os.environ.get('MATERIALIDAD_STATE_MACHINE_ARN')
        
        # Saneamos el string mapeando guiones bajos (_) a guiones medios (-) permitidos por AWS
        contrato_saneado = str(contrato).replace('_', '-')
        rfc_saneado = str(rfc_cliente).replace('_', '-')
        timestamp_saneado = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        nombre_ejecucion = f"EXEC-{rfc_saneado}-{contrato_saneado}-{timestamp_saneado}"
        # Recortamos el excedente por si el string rebasa el límite de 80 caracteres de AWS
        nombre_ejecucion = nombre_ejecucion[:75].upper()
        
        input_payload = {
            "tenant_id": tenant_id,
            "rfc_cliente": rfc_cliente,
            "nombre_cliente": nombre_cliente,
            "contrato": contrato,
            "ano_fiscal": ano_fiscal,
            "tipo_flujo": tipo_flujo
        }

        print(f"🔥 Gatillando Step Function de Materialidad Saneada: {nombre_ejecucion}")
        response = states_client.start_execution(
            stateMachineArn=state_machine_arn,
            name=nombre_ejecucion,
            input=json.dumps(input_payload)
        )

        return {
            'statusCode': 202, # 202 Accepted en minúscula para cumplir con API Gateway Proxy
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
