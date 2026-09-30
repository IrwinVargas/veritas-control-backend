import json
import boto3
import os
import datetime

# Inicialización atómica de infraestructura en la raíz del archivo (Inmune a fallas de build)
eventbridge_client = boto3.client('events')
dynamodb_resource = boto3.resource('dynamodb')

BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'Veritas-Enterprise-EventBus')
TABLE_NAME = os.environ.get('TENANTS_TABLE_NAME', 'Veritas_Tenants_Config')
tenants_table = dynamodb_resource.Table(TABLE_NAME)

def handler(event, context):
    print(f"📥 [Admin Subsystem] Procesando alta de bufete en tabla: {TABLE_NAME}")

    # 1. 🛡️ ADUANA PERIMETRAL DE PRIVILEGIOS SUPER-ADMIN (JWT COGNITO)
    request_context = event.get('requestContext', {})
    authorizer = request_context.get('authorizer', {})
    claims = authorizer.get('claims', {})
    
    if 'SUPER_ADMIN' not in claims.get('cognito:groups', '') and claims.get('custom:role', '') != 'SuperAdmin':
        return {
            'statusCode': 403,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Acceso denegado. Se requiere rol de SuperAdmin.'})
        }

    try:
        payload_data = json.loads(event.get('body', '{}'))
        nombre_bufete = payload_data.get('nombre_bufete')
        socio_admin = payload_data.get('socio_admin')
        correo_admin = payload_data.get('correo_admin')
        
        if not nombre_bufete or not socio_admin or not correo_admin:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Campos obligatorios ausentes.'})
            }

        tenant_id = f"tenant-uuid-{int(datetime.datetime.now().timestamp())}"
        costo_membresia = float(payload_data.get("costo", 0.0))
        plan_membresia = payload_data.get("plan", "ENTERPRISE")
        frecuencia = payload_data.get("frecuencia", "MENSUAL")

        # =========================================================================
        # 🚀 LA REPARACIÓN MAESTRA: Sembramos el registro base de forma síncrona.
        # Así, cuando el front haga GET de inmediato, los datos ya existirán en Dynamo.
        # =========================================================================
        print(f"⏳ Asentando registro comercial in-line para {tenant_id} en DynamoDB...")
        tenants_table.put_item(
            Item={
                'tenant_id': tenant_id,
                'razon_social': nombre_bufete,
                'nombre_comercial': nombre_bufete,
                'socio_root_name': socio_admin,
                'socio_root_email': correo_admin,
                'plan_membresia': plan_membresia,
                'costo_membresia': str(costo_membresia), # Guardado como string/número seguro
                'frecuencia_facturacion': frecuencia,
                'fecha_ultimo_pago': datetime.date.today().isoformat(),
                'fecha_proximo_pago': (datetime.date.today() + datetime.timedelta(days=30)).isoformat(),
                'estatus_infraestructura': 'ACTIVO',
                'usuarios_contador_event_driven': 1 # Inicializa la cuenta para el GET
            }
        )
        print("✅ Registro base guardado con éxito en DynamoDB.")

        # 2. 📡 PITAZO ASÍNCRONO: Avisamos a EventBridge para que corra el resto en paralelo
        event_payload = {
            "tenant_id": tenant_id,
            "nombre_bufete": nombre_bufete,
            "socio_admin_name": socio_admin,
            "socio_admin_email": correo_admin,
            "config_membresia": {"plan": plan_membresia, "costo": costo_membresia, "frecuencia": frecuencia},
            "timestamp_alta": datetime.datetime.now().isoformat()
        }

        eventbridge_client.put_events(
            Entries=[{
                'Source': 'veritas.admin.subsystem',
                'DetailType': 'TenantCreated',
                'Detail': json.dumps(event_payload),
                'EventBusName': BUS_NAME
            }]
        )

        # 3. RESPUESTA HOMOLOGADA PARA EL FRONT-END
        response_front = {
            "id": tenant_id,
            "nombreBufete": nombre_bufete,
            "socioAdmin": socio_admin,
            "correoAdmin": correo_admin,
            "usuariosRegistrados": 1,
            "planAfiliado": plan_membresia,
            "costoMembresia": costo_membresia,
            "frecuenciaPago": frecuencia,
            "ultimaFechaPago": datetime.date.today().isoformat(),
            "proximaFechaPago": (datetime.date.today() + datetime.timedelta(days=30)).isoformat(),
            "estatusApp": "ACTIVO"
        }

        return {
            'statusCode': 202,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps(response_front)
        }

    except Exception as error:
        print(f"🛑 Falla crítica en alta de bufete: {str(error)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Error en la infraestructura AWS', 'detalle': str(error)})
        }
