import os
import json
import boto3
import pg8000

# Inicializamos el búnker NoSQL interno de forma segura dentro de la VPC
dynamodb = boto3.resource('dynamodb')
_db_connection_step1 = None

def obtener_conexion_postgres_step1():
    """
    [ENFOQUE LOCAL PURO] Abre el socket TCP relacional en microsegundos fijos 
    leyendo directamente las variables que tú ya resolviste desde el template.yml.
    """
    global _db_connection_step1
    if _db_connection_step1 and not _db_connection_step1.is_closed:
        return _db_connection_step1

    # 🚀 SUCCIÓN CRUDA SUPREMA: Jalamos exactamente tus variables de entorno limpias
    host_real   = os.environ.get('DB_HOST')
    db_name     = os.environ.get('DB_NAME')
    db_user     = os.environ.get('DB_USER')
    db_port_str = os.environ.get('DB_PORT')
    db_password = os.environ.get('DB_PASSWORD')

    print(f"🔌 [Paso 1] Estableciendo socket TCP interno de la VPC: {host_real}:{db_port_str}")
    _db_connection_step1 = pg8000.connect(
        host=host_real,
        port=int(db_port_str),
        user=db_user,
        database=db_name,
        password=db_password,
        timeout=5
    )
    return _db_connection_step1

def handler(event, context):
    print("📡 Paso 1 Activo: Extrayendo transacciones del SAT bajo el Enfoque Modular Puro...")
    
    tenant_id = event.get('tenant_id')
    rfc_cliente = event.get('rfc_cliente')
    ano_fiscal = event.get('ano_fiscal', '2026')
    contrato = event.get('contrato')
    tipo_flujo = event.get('tipo_flujo', 'PREVENTIVO')

    # Succionamos el nombre de la tabla NoSQL inyectado localmente
    nombre_tabla_nosql = os.environ.get('DYNAMODB_TABLE')
    table = dynamodb.Table(nombre_tabla_nosql)
    hash_key = f"{tenant_id}#{rfc_cliente}#{contrato}#{ano_fiscal}"

    # 📊 UX SYNCHRONIZER: Dejamos pre-firmado el progreso en la Main Table de DynamoDB
    table.update_item(
        Key={'tenant_rfc_year_contract': hash_key},
        UpdateExpression="SET progreso_porcentaje = :p, mensaje_progreso = :m, estatus_global = :e",
        ExpressionAttributeValues={
            ':p': 25, 
            ':m': "Extrayendo transacciones relacionales y CFDIs oficiales desde PostgreSQL...",
            ':e': 'PROCESANDO'
        }
    )

    event['string_catalogo_ia'] = "Catálogo de soluciones por contrato preventivo."
    
    if tipo_flujo == "RECONSTRUCTIVO":
        print(f"🕵️ Flujo Reconstructivo activado. Extrayendo CFDIs históricos para RFC: {rfc_cliente}")
        
        # Se conecta de forma supersónica sin requerir internet ni brincos de SSM por red
        conn = obtener_conexion_postgres_step1()
        cursor = conn.cursor()
        
        query = "SELECT descripcion FROM facturas_sat WHERE tenant_id = %s AND rfc_receptor = %s;"
        cursor.execute(query, (tenant_id, rfc_cliente))
        rows = cursor.fetchall()
        
        # Consolidamos los conceptos de las facturas en un solo string masivo para Claude 4.5
        conceptos_unicos = list(set([str(r[0]).strip() for r in rows if r[0]]))
        event['string_catalogo_ia'] = " | ".join(conceptos_unicos)[:5000] # Cap de cortesía
        
        cursor.close()
        print(f"✅ Extracción relacional completada: {len(rows)} renglones succionados y purificados.")

    # Avanza de forma asíncrona hacia el Paso 2 (Claude 4.5 Haiku en Bedrock)
    return event