# lambdas/materialidad/preventivo_cotizacion_handler.py
import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
TABLA_NAME = os.environ.get('TABLA_MATERIALIDAD')

def handler(event, context):
    print("--- EVENTO RECIBIDO EN COTIZACIÓN (BACKEND) ---")
    print(json.dumps(event))
    
    try:
        if not TABLA_NAME:
            raise ValueError("La variable de entorno 'TABLA_MATERIALIDAD' no está configurada.")

        body_raw = event.get('body')
        if not body_raw:
            return build_response(400, {"error": "El cuerpo de la petición está vacío."})
            
        body = json.loads(body_raw)
        
        rfc = body.get('rfc')
        nombre_cliente = body.get('nombre')
        objeto_entregable = body.get('objeto_entregable', 'INTANGIBLE')
        rama_especialidad = body.get('rama_especialidad', 'CONSER_FISCAL')
        inversion_inicial = body.get('inversion_inicial', 0)
        monto_contrato = body.get('monto_contrato', 0)
        duracion_meses = body.get('duracion_meses', 12)
        nombre_enlace = body.get('nombre_enlace')
        telefono_contacto = body.get('telefono_contacto')
        tipo_notificacion = body.get('tipo_notificacion', 'INICIO')

        if not rfc or not nombre_enlace or not telefono_contacto:
            return build_response(400, {"error": "Faltan parámetros obligatorios."})

        # 🔐 MULTI-TENANT EXACTO: Extraemos el custom:tenant_id de Cognito tal cual lo hace tu lector
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        tenant_id = authorizer.get('custom:tenant_id')
        usuario_id = authorizer.get('sub', 'SISTEMA_ANONIMO')

        if not tenant_id:
            return build_response(400, {"error": "No se pudo identificar el tenant_id del token de Cognito."})

        # 🔑 UNIFICACIÓN DE HASH KEY: Mismo formato "TENANT#RFC" que usa tu listar_archivos_handler
        hash_key = f"{tenant_id}#{rfc.upper().strip()}"
        timestamp_utc = datetime.utcnow().isoformat() + 'Z'
        
        # 📂 INICIALIZACIÓN DEL MAPA DE ARCHIVOS: 
        # Inyectamos el nodo comercial y dejamos listo el benchmarking para que React conmute de paso
        item_dynamo = {
            'tenant_rfc': hash_key, # Llave unificada
            'estatus_expediente': 'PROCESANDO',
            'nombre_cliente': nombre_cliente,
            'fecha_registro': timestamp_utc,
            'registrado_por': usuario_id,
            'datos_comerciales': {
                'objeto_entregable': objeto_entregable,
                'rama_especialidad': rama_especialidad,
                'inversion_inicial': int(inversion_inicial),
                'monto_contrato': int(monto_contrato),
                'duracion_meses': int(duracion_meses),
                'nombre_enlace': nombre_enlace.strip(),
                'telefono_contacto': telefono_contacto.strip(),
                'tipo_notificacion': tipo_notificacion
            },
            'archivos': {
                'cotizacion': {
                    'status': 'COMPLETO',
                    'updated_at': timestamp_utc
                },
                'benchmarking': {
                    'status': 'PENDIENTE', # Al estar PENDIENTE, React forzará el render de la Etapa 2
                    'updated_at': timestamp_utc
                }
            }
        }

        print(f"Insertando Item Multi-tenant en '{TABLA_NAME}': {json.dumps(item_dynamo)}")

        tabla = dynamodb.Table(TABLA_NAME)
        tabla.put_item(Item=item_dynamo)
        
        print(f"✅ Éxito: Registro Multi-tenant insertado para la llave {hash_key}")

        return build_response(200, {
            "message": "Cotización sellada correctamente de forma multi-tenant.",
            "tenant_rfc": hash_key
        })

    except Exception as e:
        print(f"💥 ERROR JURÍDICO BACKEND: {str(e)}")
        return build_response(500, {"error": "Internal Server Error", "mensaje": str(e)})

def build_response(status_code, body_data):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'OPTIONS,POST'
        },
        'body': json.dumps(body_data)
    }
