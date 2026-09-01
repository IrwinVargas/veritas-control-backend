# backend/lambdas/finanzas_dashboard/carga_postgres_handler.py
import os
import json
import pg8000.dbapi

_db_connection = None

def obtener_conexion_db():
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
    try:
        payload_parser = event if isinstance(event, dict) else json.loads(event)
        tenant_id = payload_parser.get('tenant_id')
        facturas = payload_parser.get('facturas', [])

        print(f"Microservicio Postgres v3 activado. Procesando inyección para el tenant: [{tenant_id}]")

        facturas_a_insertar = []
        for row in facturas:
            # 🚀 SOLUCIÓN REINA: Forzamos el mapeo usando las llaves del SAT en minúsculas 
            # sincronizadas de forma exacta con la salida limpia que generó el ParserS3Lambda
            uuid = str(row.get('folio fiscal', row.get('folio_fiscal', ''))).strip()
            if not uuid or uuid == 'None' or uuid == '': 
                continue

            fecha_str = str(row.get('fecha y hora timbrado', row.get('fecha_hora_timbrado', '1970-01-01 00:00:00')))

            # Limpiador polimórfico de importes monetarios ($11.553,70 -> 11553.70)
            def safe_float(val):
                if val is None: return 0.0
                try:
                    val_str = str(val).strip().replace('$', '')
                    # Si el formato viene con puntos en miles y comas en centavos
                    if ',' in val_str and '.' in val_str:
                        val_str = val_str.replace('.', '').replace(',', '.')
                    elif ',' in val_str and '.' not in val_str:
                        val_str = val_str.replace(',', '.')
                    return float(val_str)
                except:
                    return 0.0

            # Estructuración exacta de la tupla relacional
            facturas_a_insertar.append((
                tenant_id, 
                str(row.get('folio', '')), 
                fecha_str,
                str(row.get('rfc emisor', '')).upper().strip(), 
                str(row.get('nombre emisor', '')),
                str(row.get('rfc receptor', '')).upper().strip(), 
                str(row.get('nombre receptor', '')),
                str(row.get('descripcion', '')),
                safe_float(row.get('sub total')), 
                safe_float(row.get('total impuestos trasladados iva', row.get('total_iva', 0.0))), 
                safe_float(row.get('total')),
                str(row.get('forma pago', '')), 
                str(row.get('metodo pago', '')), 
                str(row.get('moneda', 'MXN')),
                str(row.get('regimen fiscal receptor', '')), 
                str(row.get('domicilio fiscal receptor', '')),
                str(row.get('serie', '')), 
                str(row.get('uso cfdi', '')), 
                str(row.get('clave prod serv', '')),
                safe_float(row.get('cantidad', 1.0)), 
                str(row.get('clave unidad', '')), 
                str(row.get('unidad', '')),
                str(row.get('tipo de comprobante', 'I')).upper().strip(), 
                uuid,
                str(row.get('sello cfd', '')), 
                str(row.get('no certificado sat', '')), 
                str(row.get('sello sat', ''))
            ))
        print(f"✅ Preparación completa: {len(facturas_a_insertar)} transacciones monetarias purificadas listas para Postgres.")
        if facturas_a_insertar:
            print("🔗 Estableciendo conexión segura con la base de datos Postgres..." )
            conn = obtener_conexion_db()
            cursor = conn.cursor()
            print("🛡️ Conexión establecida. Iniciando inyección de datos históricos del SAT a Postgres..."  )
            
            # 🚀 CORRECCIÓN DE COLUMNA: Cambiamos no_certified_sat por no_certificado_sat
            query_upsert = """
                INSERT INTO facturas_sat (
                    tenant_id, folio, fecha_hora_timbrado, rfc_emisor, nombre_emisor, 
                    rfc_receptor, nombre_receptor, descripcion, sub_total, total_iva, 
                    total, forma_pago, metodo_pago, moneda, regimen_fiscal_receptor, 
                    domicilio_fiscal_receptor, serie, uso_cfdi, clave_prod_serv, cantidad, 
                    clave_unitario, unidad, tipo_de_comprobante, folio_fiscal_uuid, sello_cfd, 
                    no_certificado_sat, sello_sat
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (tenant_id, folio_fiscal_uuid) DO NOTHING;
            """

            print(f"🧹 Inyectando en lote {len(facturas_a_insertar)} transacciones monetarias purificadas a Postgres...")
            cursor.executemany(query_upsert, facturas_a_insertar)
            conn.commit()
            cursor.close()
            conn.close()
            print("💾 Datos históricos del SAT indexados con montos reales de forma exitosa.")

        return {"success": True, "count": len(facturas_a_insertar)}
    except Exception as e:
        print(f"❌ Error crítico en microservicio Postgres: {str(e)}")
        raise e
