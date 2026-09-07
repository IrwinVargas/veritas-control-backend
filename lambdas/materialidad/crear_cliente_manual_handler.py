# lambdas/materialidad/crear_cliente_manual_handler.py
import os
import json
import uuid
import boto3
import pg8000
from datetime import datetime

ssm_client = boto3.client('ssm')
dynamodb = boto3.resource('dynamodb')
_CACHED_DB_HOST = None

def resolver_endpoint_rds_dinamico():
    global _CACHED_DB_HOST
    if _CACHED_DB_HOST:
        return _CACHED_DB_HOST
    param_path_host = os.environ.get('DB_HOST_PARAM')
    try:
        response = ssm_client.get_parameter(Name=param_path_host, WithDecryption=False)
        _CACHED_DB_HOST = response['Parameter']['Value'].strip()
        return _CACHED_DB_HOST
    except Exception as e:
        print(f"❌ Error crítico resolviendo el host en el Parameter Store: {str(e)}")
        raise e

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

        # 📥 CAPTURA COMPLETA DE LA CÉLULA CORPORATIVA EXPANDIDA EN TU FRONTEND
        body = json.loads(event.get('body', '{}'))
        rfc = str(body.get('rfc', '')).strip().upper()
        nombre = str(body.get('nombre', '')).strip()
        nombre_contacto = str(body.get('nombre_contacto', '')).strip()
        telefono = str(body.get('telefono', '')).strip()
        correo_contacto = str(body.get('correo_contacto', '')).strip()
        correo_empresa = str(body.get('correo_empresa', '')).strip()
        tipo_contrato = str(body.get('tipo_contrato', 'PRESTACION_SERVICIOS')).strip().upper()
        ano_fiscal_actual = str(datetime.now().year)
        ano_fiscal = str(body.get('ano_fiscal', ano_fiscal_actual)) # Captura el año dinámico seleccionado en el select

        if not tenant_id or not rfc or not nombre:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'RFC y Razón Social son campos estrictamente requeridos.'})}

        # =========================================================================
        # 🚀 REPARACIÓN COMPUERTA 1: PERSISTENCIA EN EL BÚNKED DYNAMODB NOSQL
        # Guardamos la célula de contacto y el tipo de contrato para uso de los Prompts
        # =========================================================================
        nombre_tabla_nosql = os.environ.get('DYNAMODB_TABLE')
        table_nosql = dynamodb.Table(nombre_tabla_nosql)
        
        # Estructuramos la clave compuesta anual inmutable de Veritas
        hash_key_nosql = f"{tenant_id}#{rfc}#{tipo_contrato}#{ano_fiscal}"
        print(f"💾 Fundando registro maestro NoSQL de contacto: {hash_key_nosql}")
        
        table_nosql.put_item(
            Item={
                'tenant_rfc_year_contract': hash_key_nosql,
                'rfc_cliente': rfc,
                'nombre_cliente': nombre,
                'ano_fiscal': ano_fiscal,
                'contrato_tipo': tipo_contrato,
                'tipo_flujo': 'PREVENTIVO', # Al ser alta manual, nace por defecto en preventivo secuencial
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
        # 🚀 REPARACIÓN COMPUERTA 2: MATRIZ DE COMPATIBILIDAD RELACIONAL (POSTGRES)
        # Satisface el catálogo de facturación core para que figure en el Sidebar
        # =========================================================================
        db_host_real = resolver_endpoint_rds_dinamico()
        db_name = os.environ.get('DB_NAME', 'veritas_db')
        db_user = os.environ.get('DB_USER', 'veritas_admin')
        db_port = int(os.environ.get('DB_PORT', 5432))
        db_password = os.environ.get('DB_PASSWORD')

        print(f"🔌 Abriendo túnel TCP hacia PostgreSQL en: {db_host_real}")
        conn = pg8000.connect(host=db_host_real, database=db_name, user=db_user, password=db_password, port=db_port)
        cursor = conn.cursor()

        # Evitamos la violación Not-Null de TablePlus inyectando un folio sintético manual
        folio_manual_uuid = f"MANUAL-{str(uuid.uuid4()).upper()}"

        query_insert = """
            INSERT INTO facturas_sat (
                tenant_id, rfc_emisor, rfc_receptor, nombre_receptor, folio_fiscal_uuid,
                fecha_hora_timbrado, sub_total, total_iva, total, tipo_de_comprobante
            ) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 0.00, 0.00, 0.00, 'I');
        """
        cursor.execute(query_insert, (tenant_id, bufete_rfc.upper().strip(), rfc, nombre, folio_manual_uuid))
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
        print(f"❌ Crash en microservicio de alta manual expandido: {str(e)}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
