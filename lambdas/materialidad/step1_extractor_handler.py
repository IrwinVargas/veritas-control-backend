import os
import json
import boto3
import pg8000

ssm_client = boto3.client('ssm')
dynamodb = boto3.resource('dynamodb')

_CACHED_DB_HOST = None

def handler(event, context):
    global _CACHED_DB_HOST
    print("📡 Paso 1 Activo: Extrayendo transacciones relacionales del SAT dentro de la VPC...")
    
    # Capturamos el ticket de la cola SQS
    tenant_id = event.get('tenant_id')
    rfc_cliente = event.get('rfc_cliente')
    ano_fiscal = event.get('ano_fiscal', '2026')
    contrato = event.get('contrato')
    tipo_flujo = event.get('tipo_flujo', 'PREVENTIVO')

    # Actualizamos progreso inicial NoSQL a 25%
    hash_key = f"{tenant_id}#{rfc_cliente}#{contrato}#{ano_fiscal}"
    table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE'))
    table.update_item(
        Key={'tenant_rfc_year_contract': hash_key},
        UpdateExpression="SET progreso_porcentaje = :p, mensaje_progreso = :m, estatus_global = :e",
        ExpressionAttributeValues={
            ':p': 25, 
            ':m': "Extrayendo transacciones y CFDIs oficiales del SAT...",
            ':e': 'PROCESANDO'
        }
    )

    string_catalogo_ia = ""
    catalogo_json_payload = []

    if tipo_flujo == 'RECONSTRUCTIVO':
        if not _CACHED_DB_HOST:
            _CACHED_DB_HOST = ssm_client.get_parameter(Name=os.environ.get('DB_HOST_PARAM'), WithDecryption=False)['Parameter']['Value'].strip()
        
        conn = pg8000.connect(host=_CACHED_DB_HOST, database=os.environ.get('DB_NAME'), user=os.environ.get('DB_USER'), port=int(os.environ.get('DB_PORT', 5432)))
        cursor = conn.cursor()
        query = "SELECT descripcion, sub_total FROM facturas_sat WHERE tenant_id = %s AND rfc_receptor = %s LIMIT 15;"
        cursor.execute(query, (tenant_id, rfc_cliente))
        
        for desc, sub in cursor.fetchall():
            string_catalogo_ia += f"- {desc} (${float(sub):,.2f} MXN)\n"
            catalogo_json_payload.append({"desc": str(desc), "precio": float(sub)})
        cursor.close()
        conn.close()
    else:
        # Preventivo: Succiona de DynamoDB
        expediente = table.get_item(Key={'tenant_rfc_year_contract': hash_key}).get('Item', {})
        for prod in expediente.get('catalogo_benchmarking', []):
            amp = prod.get('amplitud_linea', 'Solución')
            prof = prod.get('profundidad_presentacion', 'U.M.')
            prec = float(prod.get('precio_lista', 0.00))
            string_catalogo_ia += f"- {amp} {prof} (${prec:,.2f})\n"
            catalogo_json_payload.append({"desc": f"{amp} {prof}", "precio": prec, "key_foto": prod.get('key_imagen_s3', '')})

    if not catalogo_json_payload:
        string_catalogo_ia = "- Planificación de Estructuras Generales de Compliance.\n"
        catalogo_json_payload.append({"desc": "Planificación Estratégica Preliminar", "precio": 0.00})

    # Pasamos de forma limpia el payload unificado al paso 2 de la Step Function
    event['string_catalogo_ia'] = string_catalogo_ia
    event['catalogo_json_payload'] = catalogo_json_payload
    return event