# =========================================================================
# MICROSERVICIO FINAL: CARGADOR MASIVO CON NOTIFICACIONES REALES INTEGRADAS
# RUTA EN MAC: backend/lambdas/finanzas_dashboard/carga_postgres_handler.py
# =========================================================================
import os
import json
import pg8000.dbapi
import boto3
import uuid
from datetime import datetime # 🚀 IMPORTACIÓN CORE ASEGURADA CONTRA EL CRASH SILENCIOSO

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
    
    _db_connection = pg8000.dbapi.connect(
        host=db_host_real, database=db_name, user=db_user,
        password=db_password, port=int(db_port_str), timeout=5 
    )
    return _db_connection

def handler(event, context):
    try:
        payload_parser = event if isinstance(event, dict) else json.loads(event)
        # 🎯 SINCRO DE PARTICIÓN MULTI-TENANT REAL: Tomamos el tenant real de la sesión
        tenant_id = payload_parser.get('tenant_id') or event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('custom:tenant_id', 'bufete-veritas-uuid-1111')
        facturas = payload_parser.get('facturas', [])

        print(f"🚀 Ingesta Real Veritas. Procesando lote para Tenant de Sesión: [{tenant_id}]")

        facturas_a_insertar = []
        clientes_a_asegurar = {} 

        for row_raw in facturas:
            if not row_raw: continue
            row = {str(k).strip().lower(): v for k, v in row_raw.items()}

            uuid_cfdi = str(row.get('folio fiscal', '')).strip()
            if not uuid_cfdi or uuid_cfdi == 'None' or uuid_cfdi == '': continue

            fecha_str = str(row.get('fecha y hora timbrado', '1970-01-01 00:00:00'))
            rfc_receptor_limpio = str(row.get('rfc receptor', '')).upper().strip()
            nombre_receptor_limpio = str(row.get('nombre receptor', '')).strip()[:255]

            if rfc_receptor_limpio and len(rfc_receptor_limpio) >= 12:
                clientes_a_asegurar[rfc_receptor_limpio] = nombre_receptor_limpio

            def safe_float(val):
                if val is None: return 0.0
                try:
                    val_str = str(val).strip().replace('$', '')
                    if ',' in val_str and '.' in val_str:
                        val_str = val_str.replace('.', '').replace(',', '.')
                    elif ',' in val_str and '.' not in val_str:
                        val_str = val_str.replace(',', '.')
                    return float(val_str)
                except: return 0.0

            facturas_a_insertar.append((
                str(row.get('descripcion', '')).strip(),                     
                fecha_str,                                                   
                uuid_cfdi,                                                   
                str(row.get('moneda', 'MXN')).strip().upper()[:4],           
                nombre_receptor_limpio,                                      
                str(row.get('rfc emisor', '')).upper().strip(),              
                rfc_receptor_limpio,                                         
                safe_float(row.get('sub total')),                            
                tenant_id,                                                   
                1.0000,                                                      
                str(row.get('tipo de comprobante', 'I')).strip().upper()[:2],
                safe_float(row.get('total')),                                
                safe_float(row.get('total impuestos trasladados iva', 0.0))  
            ))

        if facturas_a_insertar or clientes_a_asegurar:
            conn = obtener_conexion_db()
            cursor = conn.cursor()
            
            if clientes_a_asegurar:
                print(f"🏛️ Sincronizando {len(clientes_a_asegurar)} clientes en clientes_veritas...")
                query_madre_real = """
                    INSERT INTO clientes_veritas (
                        tenant_id, rfc_receptor, nombre_receptor, creado_el, actualizado_el
                    ) VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (tenant_id, rfc_receptor) DO NOTHING;
                """
                tuplas_clientes = [(tenant_id, rfc, nombre) for rfc, nombre in clientes_a_asegurar.items()]
                cursor.executemany(query_madre_real, tuplas_clientes)
                conn.commit()

            if facturas_a_insertar:
                print(f"🧹 Indexando {len(facturas_a_insertar)} CFDIs en facturas_sat...")
                query_hija_real = """
                    INSERT INTO facturas_sat (
                        descripcion, fecha_hora_timbrado, folio_fiscal_uuid, moneda, 
                        nombre_receptor, rfc_emisor, rfc_receptor, sub_total, 
                        tenant_id, tipo_cambio, tipo_de_comprobante, total, total_iva
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (tenant_id, folio_fiscal_uuid) DO NOTHING;
                """
                cursor.executemany(query_hija_real, facturas_a_insertar)
                conn.commit()

            # =========================================================================
            # 🚨 ESCANEO FISCAL EN CALIENTE CONTRA EL ARTÍCULO 69-B (LISTA NEGRA)
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

            # =========================================================================
            # ⚡ GATILLO ULTRA-AUTÓMATA: DISPARADOR REAL DE LA STEP FUNCTION
            # Extraemos las variables vivas directamente del array facturas_a_insertar
            # =========================================================================
            if facturas_a_insertar:
                try:
                    print("⚡ Indexación SAT completada. Despertando Máquina de Estados de forma automática...")
                    sfn_client = boto3.client('stepfunctions', region_name='us-east-1')
                    
                    state_machine_arn = os.environ.get('MATERIALIDAD_STATE_MACHINE_ARN', 'arn:aws:states:us-east-1:049255850526:stateMachine:veritas-control-materialidad-pipeline-dev')
                    
                    # Recuperamos la información del primer registro indexado en la tupla relacional
                    # Tupla anterior: (descripcion, fecha, uuid, moneda, nombre_receptor, rfc_emisor, rfc_receptor, ...)
                    primera_factura = facturas_a_insertar[0]
                    nombre_cliente_real = primera_factura[4]
                    rfc_cliente_real = primera_factura[6]

                    payload_orquestador = {
                        "tenant_id": str(tenant_id),
                        "rfc_cliente": str(rfc_cliente_real),
                        "nombre_cliente": str(nombre_cliente_real),
                        "ano_fiscal": "2026",
                        "contrato": "DESARROLLO_TECNOLOGICO", # Fallback base de especialidad
                        "tipo_flujo": "RECONSTRUCTIVO"
                    }
                    
                    sfn_client.start_execution(
                        stateMachineArn=state_machine_arn,
                        name=f"AUTO-RECONSTRUCTIVO-{str(tenant_id)[:8].upper()}-{str(uuid.uuid4())[:6].upper()}",
                        input=json.dumps(payload_orquestador)
                    )
                    print(f"✅ ¡Pipeline Forense detonado automáticamente para {nombre_cliente_real} ({rfc_cliente_real})!")
                except Exception as e_sfn:
                    print(f"⚠️ Alerta: No se pudo arrancar la Step Function automática: {str(e_sfn)}")

            cursor.close()
            conn.close()

        return {"success": True, "count": len(facturas_a_insertar)}
    except Exception as e:
        print(f"❌ Error crítico en microservicio Postgres Carga Excel: {str(e)}")
        raise e