import os
import json
import pg8000.dbapi

_db_connection = None

def obtener_conexion_db():
    global _db_connection
    if _db_connection and not _db_connection.is_closed: 
        return _db_connection
        
    db_host_real = os.environ.get('DB_HOST')
    db_port_str  = os.environ.get('DB_PORT', '5432')
    db_user      = os.environ.get('DB_USER')
    db_name      = os.environ.get('DB_NAME')
    db_password  = os.environ.get('DB_PASSWORD')
    
    print(f"🔌 [Carga Excel] Conectando de forma interna a la VPC a través de: {db_host_real}:{db_port_str}")
    _db_connection = pg8000.dbapi.connect(
        host=db_host_real,
        database=db_name,
        user=db_user,
        password=db_password,
        port=int(db_port_str),
        timeout=5 
    )
    return _db_connection

def handler(event, context):
    try:
        payload_parser = event if isinstance(event, dict) else json.loads(event)
        tenant_id = payload_parser.get('tenant_id')
        facturas = payload_parser.get('facturas', [])

        print(f"🚀 Microservicio Postgres Carga Excel activado. Procesando lote para Tenant: [{tenant_id}]")

        facturas_a_insertar = []
        for row_raw in facturas:
            if not row_raw:
                continue
                
            # Normalizador maestro de llaves del SAT tolerante al delimitador ";" de tu archivo real
            row = {str(k).strip().lower(): v for k, v in row_raw.items()}

            uuid_cfdi = str(row.get('folio fiscal', '')).strip()
            if not uuid_cfdi or uuid_cfdi == 'None' or uuid_cfdi == '': 
                continue

            fecha_str = str(row.get('fecha y hora timbrado', '1970-01-01 00:00:00'))

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

            # =========================================================================
            # 📐 CRUCE DE PRECISIÓN ABSOLUTA: MATCH CONTRA TU ARCHIVO DEL SAT REAL
            # La tupla mide exactamente 27 campos mapeados de forma consecutiva
            # =========================================================================
            facturas_a_insertar.append((
                tenant_id,                                                   # 1. tenant_id
                str(row.get('folio', '')).strip(),                           # 2. folio
                fecha_str,                                                   # 3. fecha_hora_timbrado
                str(row.get('rfc emisor', '')).upper().strip(),              # 4. rfc_emisor
                str(row.get('nombre emisor', '')).strip(),                   # 5. nombre_emisor
                str(row.get('rfc receptor', '')).upper().strip(),            # 6. rfc_receptor
                str(row.get('nombre receptor', '')).strip(),                 # 7. nombre_receptor
                str(row.get('descripcion', '')).strip(),                     # 8. descripcion
                safe_float(row.get('sub total')),                            # 9. sub_total
                safe_float(row.get('total impuestos trasladados iva', 0.0)), # 10. total_iva
                safe_float(row.get('total')),                                # 11. total
                str(row.get('forma pago', '')).strip(),                      # 12. forma_pago
                str(row.get('metodo pago', '')).strip().upper(),             # 13. metodo_pago
                str(row.get('moneda', 'MXN')).strip().upper(),               # 14. moneda
                str(row.get('regimen fiscal receptor', '')).strip(),         # 15. regimen_fiscal_receptor
                str(row.get('domicilio fiscal receptor', '')).strip(),       # 16. domicilio_fiscal_receptor
                str(row.get('serie', '')).strip(),                           # 17. serie
                str(row.get('uso cfdi', '')).strip().upper(),                # 18. uso_cfdi
                str(row.get('clave prod serv', '')).strip(),                 # 19. clave_prod_serv
                safe_float(row.get('cantidad', 1.0)),                        # 20. cantidad
                str(row.get('clave unidad', '')).strip().upper(),            # 21. clave_unitario (Match de espacio Corregido)
                str(row.get('unidad', '')).strip(),                          # 22. unidad
                str(row.get('tipo de comprobante', 'I')).strip().upper(),    # 23. tipo_de_comprobante
                uuid_cfdi,                                                   # 24. folio_fiscal_uuid
                str(row.get('sello cfd', '')).strip(),                       # 25. sello_cfd
                str(row.get('no certificado sat', '')).strip(),              # 26. no_certified_sat (Match Corregido)
                str(row.get('sello sat', '')).strip()                        # 27. sello_sat
            ))

        print(f"✅ Tupla purificada y auditada: {len(facturas_a_insertar)} transacciones monetarias listas para Postgres.")

        if facturas_a_insertar:
            conn = obtener_conexion_db()
            cursor = conn.cursor()
            
            # 🚀 INFRAESTRUCTURA REAL COMPILADA: 27 columnas mapeadas con 27 comodines %s simétricos
            query_upsert = """
                INSERT INTO facturas_sat (
                    tenant_id, folio, fecha_hora_timbrado, rfc_emisor, nombre_emisor, 
                    rfc_receptor, nombre_receptor, descripcion, sub_total, total_iva, 
                    total, forma_pago, metodo_pago, moneda, regimen_fiscal_receptor, 
                    domicilio_fiscal_receptor, serie, uso_cfdi, clave_prod_serv, cantidad, 
                    clave_unitario, unidad, tipo_de_comprobante, folio_fiscal_uuid, sello_cfd, 
                    no_certified_sat, sello_sat
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (tenant_id, folio_fiscal_uuid) DO NOTHING;
            """
            
            print(f"🧹 Inyectando en lote {len(facturas_a_insertar)} transacciones purificadas a Postgres...")
            cursor.executemany(query_upsert, facturas_a_insertar)
            conn.commit()
            cursor.close()
            conn.close()
            print("💾 Datos históricos del SAT indexados con éxito físico real en Postgres.")

        return {"success": True, "count": len(facturas_a_insertar)}
    except Exception as e:
        print(f"❌ Error crítico en microservicio Postgres Carga Excel: {str(e)}")
        raise e
