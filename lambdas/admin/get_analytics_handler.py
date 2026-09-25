import json
import boto3
import os

# Inicialización atómica del recurso de datos en la raíz del archivo
dynamodb_resource = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('TENANTS_TABLE_NAME', 'Veritas_Tenants_Config')
tenants_table = dynamodb_resource.Table(TABLE_NAME)

def handler(event, context):
    print("📥 [Admin Subsystem] Petición GET de analíticas recibida de forma plana")

    # 1. 🛡️ ADUANA PERIMETRAL DE PRIVILEGIOS SUPER-ADMIN (JWT COGNITO)
    request_context = event.get('requestContext', {})
    authorizer = request_context.get('authorizer', {})
    claims = authorizer.get('claims', {})
    
    cognito_groups = claims.get('cognito:groups', '')
    custom_role = claims.get('custom:role', '')

    if 'SUPER_ADMIN' not in cognito_groups and custom_role != 'SuperAdmin':
        return {
            'statusCode': 403,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Acceso denegado. Se requieren credenciales de SuperAdmin.'})
        }

    try:
        # 2. 🔍 ESCANEO DIRECTO DE CACHÉ EN DYNAMODB (Milisegundos puros)
        print(f"⏳ Escaneando tabla de control Multi-Tenant: {TABLE_NAME}...")
        response = tenants_table.scan()
        raw_items = response.get('Items', [])

        # 3. 🧠 REGLA DE NEGOCIO: Normalización in-line del listado comercial
        analytics_list = []
        for item in raw_items:
            # Estructura limpia y plana idéntica al tipado de tu rejilla Flexbox en React
            normalized_entity = {
                "id": str(item.get('tenant_id', '')),
                "nombreBufete": str(item.get('nombre_comercial', item.get('razon_social', ''))),
                "socioAdmin": str(item.get('socio_root_name', 'Socio por Asignar')),
                "correoAdmin": str(item.get('socio_root_email', 'contacto@bufete.com')),
                "usuariosRegistrados": int(item.get('usuarios_contador_event_driven', 1)), # Alimentado asíncronamente
                "planAfiliado": str(item.get('plan_membresia', 'ENTERPRISE')),
                "costoMembresia": float(item.get('costo_membresia', 0.0)),
                "frecuenciaPago": str(item.get('frecuencia_facturacion', 'MENSUAL')),
                "ultimaFechaPago": str(item.get('fecha_ultimo_pago', '')),
                "proximaFechaPago": str(item.get('fecha_proximo_pago', '2026-10-25')),
                "estatusApp": str(item.get('estatus_infraestructura', 'ACTIVO'))
            }
            analytics_list.append(normalized_entity)

        # 4. DESPACHO EXITOSO DE PRODUCCIÓN CON CABECERAS CORS LIBRES
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps(analytics_list)
        }

    except Exception as error:
        print(f"🛑 Falla crítica en lectura analítica unificada: {str(error)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Error interno en la infraestructura AWS Lambda', 'detalle': str(error)})
        }
