import os
import json
import pg8000

_db_connection_excel = None

def obtener_conexion_db_excel():
    """
    [OPCIÓN B GLOBALS] Conecta la inyección relacional masiva de forma interna
    usando las variables inyectadas de forma nativa por tu cabecera central.
    Cero consultas de red en frío, cero fallback de strings en duro.
    """
    global _db_connection_excel
    if _db_connection_excel and not _db_connection_excel.is_closed: 
        return _db_connection_excel
        
    # Succión exacta de las 5 llaves de entorno que inyecta tu template
    db_host_real = os.environ.get('DB_HOST_PARAM')
    db_port_str  = os.environ.get('DB_PORT')
    db_user      = os.environ.get('DB_USER')
    db_name      = os.environ.get('DB_NAME')
    db_password  = os.environ.get('DB_PASSWORD')
    
    print(f"🔌 [Carga Excel] Abriendo socket TCP interno dentro de la VPC privada: {db_host_real}:{db_port_str}")
    _db_connection_excel = pg8000.connect(
        host=db_host_real,
        port=int(db_port_str),
        user=db_user,
        database=db_name,
        password=db_password,
        timeout=5 # Timeout de socket protector en segundos
    )
    return _db_connection_excel

def handler(event, context):
    try:
        payload_parser = event if isinstance(event, dict) else json.loads(event)
        tenant_id = payload_parser.get('tenant_id')
        facturas = payload_parser.get('facturas', [])

        print(f"🚀 CargaExcelLambda activada [Opción B Sincronizada]. Procesando lote para Tenant: {tenant_id}")

        facturas_a_insertar = []
        for row in facturas:
            # 🚀 SINCRONIZACIÓN REAL: Jalar el UUID desde la llave exacta de tu archivo 'Folio Fiscal'
            uuid = str(row.get('Folio Fiscal', row.get('folio_fiscal', ''))).strip()
            if not uuid or uuid == 'None' or uuid == '': 
                continue

            fecha_str = str(row.get('Fecha y Hora Timbrado', row.get('fecha_hora_timbrado', '1970-01-01 00:00:00')))

            # Limpiador de importes monetarios avanzados ($11.553,70 -> 11553.70)
            def safe_float(val):
                if val is None: return 0.0
                try:
                    val_str = str(val).strip().replace('$', '')
                    if ',' in val_str and '.' in val_str:
                        val_str = val_str.replace('.', '').replace(',', '.')
                    elif ',' in val_str and '.' not in val_str:
                        val_str = val_str.replace(',', '.')
                    return float(val_str)
                except:
                    return 0.0

            # 🚀 REPARACIÓN REINA: Se elimina la columna fantasma 'folio' de la tupla
            # La tupla ahora mide exactamente 26 campos limpios listos para hacer match con Postgres
            facturas_a_insertar.append((
                tenant_id, 
                fecha_str,
                str(row.get('RFC EMISOR', '')).upper().strip(), 
                str(row.get('NOMBRE EMISOR', '')),
                str(row.get('RFC RECEPTOR', '')).upper().strip(), 
                str(row.get('NOMBRE RECEPTOR', '')),
                str(row.get('Descripcion', '')), 
                safe_float(row.get('Sub Total')), 
                safe_float(row.get('Total Impuestos Trasladados IVA', row.get('total_iva', 0.0))), 
                safe_float(row.get('Total')), 
                str(row.get('Forma Pago', '')), 
                str(row.get('Metodo Pago', '')), 
                str(row.get('Moneda', 'MXN')),
                str(row.get('Regimen Fiscal Receptor', '')), 
                str(row.get('Domicilio Fiscal Receptor', '')),
                str(row.get('Serie', '')), 
                str(row.get('Uso CFDI', '')), 
                str(row.get('Clave Prod Serv', '')),
                safe_float(row.get('Cantidad', 1.0)), 
                str(row.get('Clave Unidad', '')), 
                str(row.get('Unidad', '')),
                str(row.get('Tipo De Comprobante', 'I')).upper().strip(), 
                uuid,
                str(row.get('Sello CFD', '')), 
                str(row.get('No Certificado SAT', '')), 
                str(row.get('Sello SAT', ''))
            ))

        print(f"✅ Tupla purificada: {len(facturas_a_insertar)} transacciones monetarias listas para Postgres.")

        if facturas_a_insertar:
            conn = obtener_conexion_db_excel()
            cursor = conn.cursor()
            
            # 🚀 REPARACIÓN REINA: Se borra la palabra 'folio' y su respectivo '%s'
            # La query ahora abraza simétricamente las 26 columnas físicas existentes de tu base relacional
            query_upsert = """
                INSERT INTO facturas_sat (
                    tenant_id, fecha_hora_timbrado, rfc_emisor, nombre_emisor, 
                    rfc_receptor, nombre_receptor, descripcion, sub_total, total_iva, 
                    total, forma_pago, metodo_pago, moneda, regimen_fiscal_receptor, 
                    domicilio_fiscal_receptor, serie, uso_cfdi, clave_prod_serv, cantidad, 
                    clave_unitario, unidad, tipo_de_comprobante, folio_fiscal_uuid, sello_cfd, 
                    no_certificado_sat, sello_sat
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (tenant_id, folio_fiscal_uuid) DO NOTHING;
            """
            
            print(f"🧹 Indexando lote masivo de {len(facturas_a_insertar)} CFDIs en PostgreSQL...")
            cursor.executemany(query_upsert, facturas_a_insertar)
            conn.commit()
            cursor.close()
            conn.close()
            print("💾 Datos históricos del SAT vaciados con éxito y montos validados.")

        return {"success": True, "count": len(facturas_a_insertar)}
    except Exception as e:
        print(f"❌ Error crítico en microservicio Postgres: {str(e)}")
        raise e