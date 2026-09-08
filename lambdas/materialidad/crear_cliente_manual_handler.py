import os
import json
import uuid
import boto3
import pg8000.dbapi
from datetime import datetime

# Inicializamos el búnker de DynamoDB NoSQL (Inmune a bloqueos dentro de tu VPC)
dynamodb = boto3.resource('dynamodb')
_db_connection = None

def obtener_conexion_db():
    """
    Recicla el canal TCP relacional interno leyendo de forma directa las variables
    de entorno inyectadas de forma nativa por tu bloque de Globals.
    """
    global _db_connection
    print(_db_connection)
    if _db_connection and not _db_connection.is_closed: 
        return _db_connection
        
    _db_connection = pg8000.dbapi.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        port=int(os.environ.get('DB_PORT', 5432)),
        timeout=5 # Timeout de socket en segundos
    )
    return _db_connection

def handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    if event.get('httpMethod') == 'OPTIONS': 
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        print("📡 Extrayendo metadatos multi-tenant de Cognito...")
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        tenant_id = authorizer.get('custom:tenant_id')
        bufete_rfc = authorizer.get('custom:company_rfc', 'XAXX010101000')

        body = json.loads(event.get('body', '{}'))
        rfc = str(body.get('rfc', '')).strip().upper()
        nombre = str(body.get('nombre', '')).strip()
        nombre_contacto = str(body.get('nombre_contacto', '')).strip()
        telefono = str(body.get('telefono', '')).strip()
        correo_contacto = str(body.get('correo_contacto', '')).strip()
        correo_empresa = str(body.get('correo_empresa', '')).strip()
        tipo_contrato = str(body.get('tipo_contrato', 'PRESTACION_SERVICIOS')).strip().upper()
        tipo_flujo = str(body.get('tipo_flujo', 'PREVENTIVO')).strip().upper()
        ano_fiscal_actual = str(datetime.now().year)
        ano_fiscal = str(body.get('ano_fiscal', ano_fiscal_actual))

        if not tenant_id or not rfc or not nombre:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'RFC y Razón Social son campos estrictamente requeridos.'})}

        # =========================================================================
        # 💾 BÚNKER 1: PERSISTENCIA EN EL EXPEDIENTE NOSQL MAESTRO (DYNAMODB)
        # =========================================================================
        entorno_actual = os.environ.get('Environment', 'dev')
        nombre_tabla_nosql = os.environ.get('DYNAMODB_TABLE')
        if not nombre_tabla_nosql:
            nombre_tabla_nosql = f"veritas-control-materialidad-status-{entorno_actual}"
            
        table_nosql = dynamodb.Table(nombre_tabla_nosql)
        hash_key_nosql = f"{tenant_id}#{rfc}#{tipo_contrato}#{ano_fiscal}"
        
        table_nosql.put_item(
            Item={
                'tenant_rfc': hash_key_nosql, # Match exacto con tu Hash Key física
                'rfc_cliente': rfc,
                'nombre_cliente': nombre,
                'ano_fiscal': ano_fiscal,
                'contrato_tipo': tipo_contrato,
                'tipo_flujo': tipo_flujo,
                'progreso_porcentaje': 0,
                'estatus_global': 'PENDIENTE',
                'meta_contacto': {
                    'nombre_completo': nombre_contacto,
                    'telefono_directo': telefono,
                    'correo_enlace': correo_contacto,
                    'correo_institucional': correo_empresa
                },
                'creado_el': datetime.utcnow().isoformat() + "Z",
                'archivos': {}
            }
        )
        
        # =========================================================================
        # 🔌 BÚNKER 2: MATRIZ DE PERSISTENCIA RELACIONAL (POSTGRESQL)
        # =========================================================================
        conn = obtener_conexion_db()
        cursor = conn.cursor()

        # Prefijo de 4 caracteres + 36 del UUID = 40 caracteres fijos (character varying(40))
        folio_manual_uuid = f"MAN-{str(uuid.uuid4()).upper()}"

        # 1️⃣ PRIMERO: Aseguramos el cliente maestro relacional para no violar la Foreign Key
        query_insert_cliente = """
            INSERT INTO clientes_veritas (tenant_id, rfc_receptor, nombre_receptor, creado_el, actualizado_el)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (tenant_id, rfc_receptor) 
            DO UPDATE SET nombre_receptor = EXCLUDED.nombre_receptor, actualizado_el = CURRENT_TIMESTAMP;
        """
        cursor.execute(query_insert_cliente, (tenant_id, rfc, nombre))

        # 2️⃣ SEGUNDO: Inyectamos la factura sintética libre de la columna inexistente 'folio'
        query_insert_factura = """
            INSERT INTO facturas_sat (
                tenant_id, rfc_emisor, rfc_receptor, nombre_receptor, folio_fiscal_uuid,
                fecha_hora_timbrado, sub_total, total_iva, total, tipo_de_comprobante
            ) VALUES (
                %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 0.00, 0.00, 0.00, 'I'
            );
        """
        cursor.execute(query_insert_factura, (
            tenant_id, 
            bufete_rfc.upper().strip(), 
            rfc, 
            nombre, 
            folio_manual_uuid
        ))
        
        conn.commit()
        cursor.close()
        conn.close()

        print("Ingestión Dual Sincronizada completada con éxito rotundo.")
        return {
            'statusCode': 200, 
            'headers': headers, 
            'body': json.dumps({
                'success': True, 
                'folio_manual_uuid': folio_manual_uuid,
                'nosql_key': hash_key_nosql
            })
        }
    except Exception as e:
        print(f"❌ Error crítico en microservicio Postgres: {str(e)}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
