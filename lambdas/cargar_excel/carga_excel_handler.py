import os
import json
import pg8000
import boto3
import uuid
from datetime import datetime

_db_connection_excel = None

def obtener_conexion_db_excel():
    """
    [OPCIÓN B GLOBALS] Abre el conector relacional interno dentro de la VPC privada
    utilizando única y estrictamente las variables inyectadas por CloudFormation.
    """
    global _db_connection_excel
    if _db_connection_excel and not _db_connection_excel.is_closed: 
        return _db_connection_excel
        
    db_host_real = os.environ.get('DB_HOST')
    db_port_str  = os.environ.get('DB_PORT')
    db_user      = os.environ.get('DB_USER')
    db_name      = os.environ.get('DB_NAME')
    db_password  = os.environ.get('DB_PASSWORD')
    
    print(f"🔌 [Carga Excel] Conectando internamente a la VPC privada a través de {db_host_real}:{db_port_str}")
    _db_connection_excel = pg8000.connect(
        host=db_host_real,
        port=int(db_port_str),
        user=db_user,
        database=db_name,
        password=db_password,
        timeout=5
    )
    return _db_connection_excel


def handler(event, context):
    try:
        payload_parser = event if isinstance(event, dict) else json.loads(event)
        tenant_id = payload_parser.get('tenant_id')
        facturas = payload_parser.get('facturas', [])

        print(f"🚀 CargaExcelLambda activada [Opción B Real]. Procesando lote para Tenant: {tenant_id}")

        facturas_a_insertar = []
        for row_raw in facturas:
            if not row_raw:
                continue
                
            # Normalizador maestro de llaves del SAT tolerante al delimitador ";" de tu archivo real
            # Convierte "Fecha y Hora Timbrado" -> "fecha y hora timbrado" de forma automática
            row = {str(k).strip().lower(): v for k, v in row_raw.items()}

            # Mapeo exacto del UUID del SAT
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
            # 📐 CRUCE DE PRECISIÓN ABSOLUTA: MATCH 100% FIEL CONTRA TU ARCHIVO DEL SAT
            # La tupla mide exactamente 23 campos mapeados simétricamente con minúsculas limpias
            # =========================================================================
            facturas_a_insertar.append((
                tenant_id,                                                   # 1. tenant_id
                fecha_str,                                                   # 2. fecha_hora_timbrado
                str(row.get('rfc emisor', '')).upper().strip(),              # 3. rfc_emisor
                str(row.get('rfc receptor', '')).upper().strip(),            # 4. rfc_receptor
                str(row.get('nombre receptor', '')).strip(),                 # 5. nombre_receptor
                str(row.get('descripcion', '')).strip(),                     # 6. descripcion
                safe_float(row.get('sub total')),                            # 7. sub_total
                safe_float(row.get('total impuestos trasladados iva', 0.0)), # 8. total_iva
                safe_float(row.get('total')),                                # 9. total
                str(row.get('moneda', 'MXN')).strip().upper(),               # 10. moneda
                str(row.get('regimen fiscal receptor', '')).strip(),         # 11. regimen_fiscal_receptor
                str(row.get('domicilio fiscal receptor', '')).strip(),       # 12. domicilio_fiscal_receptor
                str(row.get('serie', '')).strip(),                           # 13. serie
                str(row.get('uso cfdi', '')).strip().upper(),                # 14. uso_cfdi
                str(row.get('clave prod serv', '')).strip(),                 # 15. clave_prod_serv
                safe_float(row.get('cantidad', 1.0)),                        # 16. cantidad
                str(row.get('clave unidad', '')).strip().upper(),            # 17. clave_unitario (Match Corregido)
                str(row.get('unidad', '')).strip(),                          # 18. unidad
                str(row.get('tipo de comprobante', 'I')).strip().upper(),    # 19. tipo_de_comprobante
                uuid_cfdi,                                                   # 20. folio_fiscal_uuid
                str(row.get('sello cfd', '')).strip(),                       # 21. sello_cfd
                str(row.get('no certificado sat', '')).strip(),              # 22. no_certified_sat
                str(row.get('sello sat', '')).strip()                        # 23. sello_sat
            ))

        print(f"✅ Tupla purificada y auditada: {len(facturas_a_insertar)} transacciones monetarias listas para Postgres.")

        if facturas_a_insertar:
            conn = obtener_conexion_db_excel()
            cursor = conn.cursor()
            
            # 🚀 INFRAESTRUCTURA RIGIDA: 23 columnas simétricas emparejadas con los %s
            query_upsert = """
                INSERT INTO facturas_sat (
                    tenant_id, fecha_hora_timbrado, rfc_emisor,  
                    rfc_receptor, nombre_receptor, descripcion, sub_total, total_iva, 
                    total, moneda, regimen_fiscal_receptor, 
                    domicilio_fiscal_receptor, serie, uso_cfdi, clave_prod_serv, cantidad, 
                    clave_unitario, unidad, tipo_de_comprobante, folio_fiscal_uuid, sello_cfd, 
                    no_certified_sat, sello_sat
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s
                )
                ON CONFLICT (tenant_id, folio_fiscal_uuid) DO NOTHING;
            """
            
            print(f"🧹 Indexando lote masivo de {len(facturas_a_insertar)} CFDIs en PostgreSQL...")
            cursor.executemany(query_upsert, facturas_a_insertar)
            conn.commit()
            print("💾 Datos históricos del SAT vaciados con éxito en Postgres.")

            # =========================================================================
            # 🚨 ESCANEO FISCAL EN CALIENTE: INTEGRIDAD CONTRA EL ARTÍCULO 69-B
            # =========================================================================
            try:
                print("🔎 Iniciando escaneo forense relacional contra la lista_negra_sat...")
                query_cross_match = """
                    SELECT DISTINCT f.rfc_receptor, f.nombre_receptor, l.situacion
                    FROM facturas_sat f
                    INNER JOIN lista_negra_sat l ON f.rfc_receptor = l.rfc
                    WHERE f.tenant_id = %s;
                """
                cursor.execute(query_cross_match, (tenant_id,))
                colisiones_detectadas = cursor.fetchall()

                # Instanciamos la persistencia NoSQL para el feed flotante del Header
                dynamodb_notif = boto3.resource('dynamodb')
                tabla_notif_name = os.environ.get('NOTIFICACIONES_TABLE', "veritas-control-notificaciones-dev")
                table_notif = dynamodb_notif.Table(tabla_notif_name)
                
                fecha_actual_unix = int(datetime.utcnow().timestamp())
                ttl_10_dias = fecha_actual_unix + (10 * 24 * 60 * 60)

                if colisiones_detectadas:
                    print(f"⚠️ ¡ALERTA ROJA JURÍDICA! Se detectaron {len(colisiones_detectadas)} colisiones con EFOS.")
                    for rfc_malo, nombre_malo, situacion_sat in colisiones_detectadas:
                        id_alerta = f"ALERT-69B-{str(uuid.uuid4())[:8].upper()}"
                        table_notif.put_item(
                            Item={
                                'tenant_id': tenant_id,
                                'notificacion_id': id_alerta,
                                'tipo': 'IA',
                                'titulo': '🚨 RIESGO Artículo 69-B:',
                                'descripcion': f"Se detectó transaccionalidad con la empresa boletinada {nombre_malo} ({rfc_malo}) en estatus de [{situacion_sat}]. Se requiere atención legal inmediata.",
                                'creado_el': datetime.utcnow().isoformat() + "Z",
                                'leido': False,
                                'fecha_expiracion': ttl_10_dias
                            }
                        )
                else:
                    print("✅ Escaneo completado: 0 colisiones detectadas. El lote de CFDIs está en verde total.")
                    id_alerta = f"NOTIF-EXCEL-{str(uuid.uuid4())[:8].upper()}"
                    table_notif.put_item(
                        Item={
                            'tenant_id': tenant_id,
                            'notificacion_id': id_alerta,
                            'tipo': 'SAT',
                            'titulo': '🏛️ Carga de CFDIs Exitosa:',
                            'descripcion': f"El archivo masivo de Excel se procesó de forma limpia e indexó {len(facturas_a_insertar)} transacciones en Postgres libres de riesgos del 69-B.",
                            'creado_el': datetime.utcnow().isoformat() + "Z",
                            'leido': False,
                            'fecha_expiracion': ttl_10_dias
                        }
                    )
            except Exception as e_cross:
                print(f"⚠️ Alerta en el motor de cruce fiscal: {str(e_cross)}")
                
            cursor.close()
            conn.close()

        return {"success": True, "count": len(facturas_a_insertar)}
    except Exception as e:
        print(f"❌ Error crítico en microservicio Postgres: {str(e)}")
        raise e
