# lambdas/cargar_excel/carga_excel_handler.py
import os
import json
import pg8000
import boto3
from datetime import datetime

_db_connection_excel = None

def obtener_conexion_db_excel():
    global _db_connection_excel
    if _db_connection_excel and not _db_connection_excel.is_closed: 
        return _db_connection_excel
        
    # 🎯 SUCCIÓN PERFECTA: Jalamos la variable de entorno que CloudFormation ya resolvió
    db_host_real = os.environ.get('DB_HOST')
    db_port_str  = os.environ.get('DB_PORT')
    db_user      = os.environ.get('DB_USER')
    db_name      = os.environ.get('DB_NAME')
    db_password  = os.environ.get('DB_PASSWORD')
    
    print(f"🔌 [Carga Excel] Conectando de forma interna a: {db_host_real}:{db_port_str}")
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
                
            # Normalizador de llaves del SAT tolerante al delimitador ";" de tu archivo real
            row = {str(k).strip().lower(): v for k, v in row_raw.items()}

            uuid = str(row.get('folio fiscal', row.get('folio_fiscal', ''))).strip()
            if not uuid or uuid == 'None' or uuid == '': 
                continue

            fecha_str = str(row.get('fecha y hora timbrado', row.get('fecha_hora_timbrado', '1970-01-01 00:00:00')))

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

            # 🚀 REPARACIÓN REINA: Se elimina 'nombre emisor' de la tupla.
            # La tupla ahora mide exactamente 25 campos limpios y simétricos listos para Postgres
            facturas_a_insertar.append((
                tenant_id, 
                fecha_str,
                str(row.get('rfc emisor', '')).upper().strip(), 
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

        print(f"✅ Tupla purificada: {len(facturas_a_insertar)} transacciones monetarias listas para Postgres.")

        if facturas_a_insertar:
            conn = obtener_conexion_db_excel()
            cursor = conn.cursor()
            
            query_upsert = """
                INSERT INTO facturas_sat (
                    tenant_id, fecha_hora_timbrado, rfc_emisor,  
                    rfc_receptor, nombre_receptor, descripcion, sub_total, total_iva, 
                    total, forma_pago, metodo_pago, moneda, regimen_fiscal_receptor, 
                    domicilio_fiscal_receptor, serie, uso_cfdi, clave_prod_serv, cantidad, 
                    clave_unitario, unidad, tipo_de_comprobante, folio_fiscal_uuid, sello_cfd, 
                    no_certified_sat, sello_sat
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s
                )
                ON CONFLICT (tenant_id, folio_fiscal_uuid) DO NOTHING;
            """
            
            print(f"🧹 Indexando lote masivo de {len(facturas_a_insertar)} CFDIs en PostgreSQL...")
            cursor.executemany(query_upsert, facturas_a_insertar)
            conn.commit() # Consolidamos las facturas de forma segura
            print("💾 Datos históricos del SAT vaciados con éxito en Postgres.")

            # =========================================================================
            # 🚀 MOTOR DE INTELIGENCIA FISCAL: CRUCE EN CALIENTE CONTRA EL ARTÍCULO 69-B
            # =========================================================================
            try:
                print("🔎 Iniciando escaneo forense relacional contra la lista_negra_sat...")
                
                # Buscamos si algún RFC receptor del lote recién cargado colisiona con el padrón del SAT
                query_cross_match = """
                    SELECT DISTINCT f.rfc_receptor, f.nombre_receptor, l.situacion
                    FROM facturas_sat f
                    INNER JOIN lista_negra_sat l ON f.rfc_receptor = l.rfc
                    WHERE f.tenant_id = %s;
                """
                cursor.execute(query_cross_match, (tenant_id,))
                colisiones_detectadas = cursor.fetchall()

                # Si el cursor regresa hileras, significa que el cliente está transaccionando con una empresa boletinada
                if colisiones_detectadas:
                    print(f"⚠️ ¡ALERTA ROJA JURÍDICA! Se detectaron {len(colisiones_detectadas)} colisiones con Listas Negras.")
                    
                    dynamodb_notif = boto3.resource('dynamodb')
                    tabla_notif_name = os.environ.get('NOTIFICACIONES_TABLE', "veritas-control-notificaciones-dev")
                    table_notif = dynamodb_notif.Table(tabla_notif_name)
                    
                    # Candado de expiración forzado: Fecha actual Unix + 10 días fijos (864,000 segundos)
                    fecha_actual_unix = int(datetime.utcnow().timestamp())
                    ttl_10_dias = fecha_actual_unix + (10 * 24 * 60 * 60)

                    for rfc_malo, nombre_malo, situacion_sat in colisiones_detectadas:
                        import uuid
                        id_alerta = f"ALERT-69B-{str(uuid.uuid4())[:8].upper()}"
                        
                        # Sembramos el push de máxima urgencia legal en el feed estilo Facebook
                        table_notif.put_item(
                            Item={
                                'tenant_id': tenant_id,          # HASH Key
                                'notificacion_id': id_alerta,    # RANGE Key
                                'tipo': 'IA',                    # Icono de Bot o Alerta Crítica
                                'titulo': '🚨 RIESGO Artículo 69-B:',
                                'descripcion': f"Se detectó transaccionalidad con la empresa boletinada {nombre_malo} ({rfc_malo}) en estatus de [{situacion_sat}]. Se requiere atención legal inmediata.",
                                'creado_el': datetime.utcnow().isoformat() + "Z",
                                'leido': False,
                                'fecha_expiracion': ttl_10_dias  # Autodestrucción automática gratuita
                            }
                        )
                else:
                    print("✅ Escaneo completado: 0 colisiones detectadas. El lote de CFDIs está en verde total.")
                    
                    # Enviamos la notificación normal de éxito que ya teníamos validada
                    dynamodb_notif = boto3.resource('dynamodb')
                    tabla_notif_name = os.environ.get('NOTIFICACIONES_TABLE', "veritas-control-notificaciones-dev")
                    table_notif = dynamodb_notif.Table(tabla_notif_name)
                    
                    fecha_actual_unix = int(datetime.utcnow().timestamp())
                    ttl_10_dias = fecha_actual_unix + (10 * 24 * 60 * 60)
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
                
            # Limpieza final de sockets relacionales
            cursor.close()
            conn.close()

        return {"success": True, "count": len(facturas_a_insertar)}
    except Exception as e:
        print(f"❌ Error crítico en microservicio Postgres: {str(e)}")
        raise e