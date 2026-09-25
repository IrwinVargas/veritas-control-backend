import json
import boto3
import os
import datetime

# Inicialización de clientes de infraestructura AWS en la raíz del archivo
# 🚀 EventBridge para despachar de forma asíncrona el flujo a Postgres, Cobros y Bienvenida
eventbridge_client = boto3.client('events')

BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'Veritas-Enterprise-EventBus')

def handler(event, context):
    print("📥 [Admin Subsystem] Petición POST de alta Multi-Tenant recibida de forma plana")

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
            'body': json.dumps({'error': 'Acceso denegado. Operación exclusiva del dueño del SaaS.'})
        }

    try:
        # 2. PARSEO DE CREDENCIALES COMERCIALES
        body_str = event.get('body', '{}')
        payload_data = json.loads(body_str)

        nombre_bufete = payload_data.get('nombre_bufete')
        socio_admin = payload_data.get('socio_admin')
        correo_admin = payload_data.get('correo_admin')
        
        if not nombre_bufete or not socio_admin or not correo_admin:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Campos obligatorios ausentes en el formulario.'})
            }

        # 3. 🧠 REGLA DE NEGOCIO: Estructuramos la Verdad del Inquilino
        tenant_id = f"tenant-uuid-{int(datetime.datetime.now().timestamp())}"
        
        # Diccionario plano nativo, inmune a fallas de tipado o empaquetado de clases externas
        event_payload = {
            "tenant_id": tenant_id,
            "nombre_bufete": nombre_bufete,
            "socio_admin_name": socio_admin,
            "socio_admin_email": correo_admin,
            "config_membresia": {
                "plan": payload_data.get("plan", "ENTERPRISE"),
                "costo": float(payload_data.get("costo", 0.0)),
                "frecuencia": payload_data.get("frecuencia", "MENSUAL")
            },
            "timestamp_alta": datetime.datetime.now().isoformat()
        }

        # 4. 🚀 EMISIÓN DE EVENTO ASÍNCRONO EN AMAZON EVENTBRIDGE
        print(f"⏳ Publicando evento TenantCreated en el bus {BUS_NAME} para el id: {tenant_id}")
        eventbridge_client.put_events(
            Entries=[
                {
                    'Source': 'veritas.admin.subsystem',
                    'DetailType': 'TenantCreated',
                    'Detail': json.dumps(event_payload),
                    'EventBusName': BUS_NAME
                }
            ]
        )

        # 5. RETORNO SÍNCRONO RESPONSIVO PARA TU REJILLA EN REACT
        # Envía la estructura exacta que traga el Front-End para pintarse al instante
        response_front = {
            "id": tenant_id,
            "nombreBufete": event_payload["nombre_bufete"],
            "socioAdmin": event_payload["socio_admin_name"],
            "correoAdmin": event_payload["socio_admin_email"],
            "usuariosRegistrados": 1, # Socio root inicial
            "planAfiliado": event_payload["config_membresia"]["plan"],
            "costoMembresia": event_payload["config_membresia"]["costo"],
            "frecuenciaPago": event_payload["config_membresia"]["frecuencia"],
            "ultimaFechaPago": datetime.date.today().isoformat(),
            "proximaFechaPago": (datetime.date.today() + datetime.timedelta(days=30)).isoformat(),
            "estatusApp": "ACTIVO"
        }

        return {
            'statusCode': 202, # Accepted: El búnker asimiló la orden y la procesa en paralelo
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps(response_front)
        }

    except Exception as error:
        print(f"🛑 Falla crítica en pasarela de aprovisionamiento admin: {str(error)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Error interno en la infraestructura AWS Lambda', 'detalle': str(error)})
        }
