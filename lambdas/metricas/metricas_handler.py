# backend/lambdas/finanzas_dashboard/metricas_handler.py
import os
import json
import boto3
from decimal import Decimal

# Inicializamos el recurso nativo de DynamoDB fuera del handler para reutilizar conexiones en caliente
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

class DecimalEncoder(json.JSONEncoder):
    """
    Helper indispensable para transformar los tipos numéricos Decimal de DynamoDB
    a tipos flotantes y enteros primitivos compatibles con el formato JSON estándar.
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Si el número tiene decimales flotantes, lo convierte a float; si es entero, a int
            return float(obj) if obj % 1 else int(obj)
        return super(DecimalEncoder, self).default(obj)

def handler(event, context):
    # Cabeceras de control CORS para que tu navegador de React (localhost) pueda leer los datos
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }

    # Interceptor manual para el Preflight del navegador
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        print("Despertando lector NoSQL para el tablero contable de Veritas Control...")
        
        # Extracción inviolable de la identidad multi-tenant desde el token de Cognito
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        tenant_id = authorizer.get('custom:tenant_id')
        user_role = authorizer.get('custom:role')

        # Candado administrativo en el servidor (RBAC)
        if user_role not in ['Socio', 'Contador']:
            return {
                'statusCode': 403,
                'headers': headers,
                'body': json.dumps({'error': 'Acceso denegado. Permisos financieros insuficientes.'})
            }

        if not tenant_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'El usuario actuante no cuenta con un identificador de bufete (tenant_id).'})
            }

        # Conexión directa a la tabla NoSQL definida en tu template.yaml
        nombre_tabla = os.environ.get('DYNAMODB_TABLE')
        table = dynamodb.Table(nombre_tabla)

        print(f"Consultando fila contable por llave primaria tenant_id: {tenant_id}")
        
        # Realizamos una lectura por llave primaria (Key-Value lookup), la operación más rápida en DynamoDB
        response = table.get_item(Key={'tenant_id': tenant_id})
        item = response.get('Item')

        # Escenario de contingencia por si el bufete es totalmente nuevo y jamás ha subido un Excel
        if not item:
            print(f"⚠️ El tenant [{tenant_id}] no registra historial financiero precalculado.")
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'success': True,
                    'metrics': {
                        'ventas_totales': 0.0,
                        'ingresos_totales': 0.0,
                        'egresos_totales': 0.0,
                        'flujo_caja': 0.0,
                        'ticket_promedio': 0.0,
                        'comisiones_totales': 0.0,
                        'margen_ganancia': 0.0,
                        'roi': 0.0,
                        'grafica_historica': []
                    }
                })
            }

        print("Registro NoSQL localizado con éxito. Construyendo ráfaga de salida...")
        
        # Retorno optimizado: Inyectamos el DecimalEncoder para que la conversión a JSON sea transparente
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'metrics': item # DynamoDB ya devuelve el mapa con el formato exacto que espera tu Front de React
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        print(f"❌ Error crítico en el extractor NoSQL de AWS: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Crash interno en el servidor de métricas: {str(e)}'})
        }
