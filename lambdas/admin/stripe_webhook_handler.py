import json
import boto3
import os
import stripe

eventbridge_client = boto3.client('events')
secrets_client = boto3.client('secretsmanager')

BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'Veritas-Enterprise-EventBus')
SECRET_NAME = os.environ.get('STRIPE_SECRET_NAME', 'Veritas-Stripe-Enterprise-Keys')

def handler(event, context):
    print(f"📥 [Stripe Webhook] Descargando llaves desde el secreto por nombre: {SECRET_NAME}")
    
    try:
        # 🧠 DESCARGA POR NOMBRE: Consumimos el búnker creado desde la consola de tu Mac
        response_secret = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        secret_dict = json.loads(response_secret['SecretString'])
        
        stripe.api_key = secret_dict.get('secret_key')
        webhook_secret = secret_dict.get('endpoint_secret')
        
    except Exception as secret_err:
        print(f"🛑 Error extrayendo secreto desde la consola AWS: {str(secret_err)}")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Falla de autorizacion financiera perimetral'})}

    headers = event.get('headers', {})
    # Stripe firma cada petición para evitar que intrusos simulen pagos exitosos
    stripe_signature = headers.get('Stripe-Signature') or headers.get('stripe-signature')
    body_str = event.get('body', '')

    if not stripe_signature:
        print("🛑 Firma de Stripe ausente en las cabeceras HTTP.")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Cabecera Stripe-Signature mandatoria ausente.'})
        }

    try:
        # 1. 🛡️ ADUANA CRÍTICA DE VERIFICACIÓN DE IDENTIDAD FINANCIERA
        # Valida matemáticamente que el evento fue emitido de verdad por Stripe
        stripe_event = stripe.Webhook.construct_event(
            body_str, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
        print(f"✅ Firma validada con éxito. Tipo de evento Stripe: {stripe_event['type']}")

        # 2. 🧠 BIFURCACIÓN DE REGLAS DE NEGOCIO DIRIGIDA POR EVENTOS
        if stripe_event['type'] == 'checkout.session.completed':
            session_data = stripe_event['data']['object']
            
            # Recuperamos las variables meta corporativas que inyectamos al crear la sesión
            metadata = session_data.get('metadata', {})
            tenant_id = metadata.get('tenant_id')
            correo_admin = metadata.get('correo_admin')
            nombre_bufete = metadata.get('nombre_bufete')
            socio_admin = metadata.get('socio_admin')

            if not tenant_id:
                print("⚠️ Sesión de Stripe completada sin tenant_id en metadata. Omitiendo activación.")
                return {'statusCode': 200, 'body': json.dumps({'status': 'ignored_no_metadata'})}

            # 3. 🚀 DISPARO EVENT-DRIVEN DEFINITIVO: Activación en Background
            # Estatus del pago confirmado. Mandamos la señal de victoria al Bus de EventBridge
            print(f"⏳ Pago exitoso confirmado. Despachando TenantActivated para: {tenant_id}")
            
            payload_activacion = {
                "tenant_id": tenant_id,
                "nombre_bufete": nombre_bufete,
                "socio_admin_name": socio_admin,
                "socio_admin_email": correo_admin,
                "stripe_subscription_id": session_data.get('subscription'),
                "stripe_customer_id": session_data.get('customer'),
                "status_pago": "COMPLETO"
            }

            eventbridge_client.put_events(
                Entries=[
                    {
                        'Source': 'veritas.finance.subsystem',
                        'DetailType': 'TenantActivated', # 👑 El evento que descongela Cognito y Postgres
                        'Detail': json.dumps(payload_activacion),
                        'EventBusName': BUS_NAME
                    }
                ]
            )

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'status': 'processed_successfully'})
        }

    except stripe.error.SignatureVerificationError as sig_error:
        print(f"🛑 Intento de hackeo o firma inválida detectada por Stripe SDK: {str(sig_error)}")
        return {'statusCode': 400, 'body': json.dumps({'error': 'Firma de Webhook fraudulenta o invalida.'})}
        
    except Exception as error:
        print(f"🛑 Falla catastrófica en procesamiento de webhook financiero: {str(error)}")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Error interno en aduana de pagos AWS', 'detalle': str(error)})}
