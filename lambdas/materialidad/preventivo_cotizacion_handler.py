# lambdas/materialidad/preventivo_cotizacion_handler.py
import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
TABLA_NAME = os.environ.get('TABLA_MATERIALIDAD')

def handler(event, context):
    print("--- EVENTO RECIBIDO DESDE API GATEWAY ---")
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
            return build_response(400, {
                "error": "Faltan parámetros obligatorios.", 
                "campos_requeridos": ["rfc", "nombre_enlace", "telefono_contacto"]
            })

        usuario_id = "SISTEMA_ANONIMO"
        request_context = event.get('requestContext', {})
        if 'authorizer' in request_context and 'claims' in request_context['authorizer']:
            usuario_id = request_context['authorizer']['claims'].get('sub', 'SISTEMA_ANONIMO')

        timestamp_utc = datetime.utcnow().isoformat() + 'Z'
        
        # 🔑 ADAPTACIÓN CRÍTICA: Mapeamos la primary key exacta a 'tenant_rfc'
        item_dynamo = {
            'tenant_rfc': rfc,  # Requisito indispensable de tu database-infra.yaml
            'expediente_id': f"EXP-{rfc}",
            'nombre_cliente': nombre_cliente,
            'objeto_entregable': objeto_entregable,
            'rama_especialidad': rama_especialidad,
            'inversion_inicial': int(inversion_inicial),
            'monto_contrato': int(monto_contrato),
            'duracion_meses': int(duracion_meses),
            'nombre_enlace': nombre_enlace.strip(),
            'telefono_contacto': telefono_contacto.strip(),
            'tipo_notificacion': tipo_notificacion,
            'registrado_por': usuario_id,
            'fecha_registro': timestamp_utc,
            'fase_actual': "COTIZACION",
            'estatus_fase': "COMPLETO"
        }

        print(f"Escribiendo en Tabla Real '{TABLA_NAME}': {json.dumps(item_dynamo)}")

        tabla = dynamodb.Table(TABLA_NAME)
        tabla.put_item(Item=item_dynamo)
        
        print(f"✅ Registro insertado exitosamente en la tabla simplificada para el RFC: {rfc}")

        return build_response(200, {
            "message": "Información de cotización guardada correctamente.",
            "expediente_id": f"EXP-{rfc}",
            "tenant_rfc": rfc
        })

    except Exception as e:
        print(f"💥 ERROR EN HANDLER MATERIALIDAD: {str(e)}")
        import traceback
        traceback.print_exc()
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
