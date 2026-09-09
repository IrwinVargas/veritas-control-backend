import os
import io
import csv
import uuid
import boto3
import pg8000
from datetime import datetime

s3_client = boto3.client('s3')

def handler(event, context):
    try:
        # Extraemos las coordenadas del evento nativo de S3
        record = event['Records'][0]
        bucket_name = record['s3']['bucket']['name']
        object_key = record['s3']['object']['key']
        
        print(f"📡 Detectado listado del SAT en S3: {object_key}. Iniciando succión masiva...")

        objeto_s3 = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        
        # Procesamos línea por línea decodificando desde S3 de forma eficiente (latin-1 para el SAT)
        lineas_flujo = io.TextIOWrapper(objeto_s3['Body'], encoding='latin-1')
        lector_lineas = csv.reader(lineas_flujo, delimiter=',')
        
        print("🔌 Abriendo socket TCP privado con la base de datos PostgreSQL dentro de la VPC...")
        conn = pg8000.connect(
            host=os.environ.get('DB_HOST'),
            database=os.environ.get('DB_NAME'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            port=int(os.environ.get('DB_PORT', 5432)),
            timeout=15
        )
        cursor = conn.cursor()

        # 🚀 REPARACIÓN REINA 1: Aseguramos la existencia física de la tabla con Primary Key rígida
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lista_negra_sat (
                numero_consecutivo INT,
                rfc VARCHAR(13) PRIMARY KEY,
                nombre_contribuyente VARCHAR(255),
                situacion VARCHAR(100),
                oficio_definitivo_sat VARCHAR(200),
                fecha_definitivo_sat VARCHAR(100)
            );
        """)
        conn.commit()

        # 🚀 REPARACIÓN REINA 2: Mutamos a UPSERT atómico para volver la query 100% idempotente
        # Evita la colisión de clave única (Primary Key Unique Constraint Violation 23505)
        query_upsert_bulk = """
            INSERT INTO lista_negra_sat (
                numero_consecutivo, rfc, nombre_contribuyente, situacion, 
                oficio_definitivo_sat, fecha_definitivo_sat
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (rfc) DO UPDATE SET
                numero_consecutivo = EXCLUDED.numero_consecutivo,
                nombre_contribuyente = EXCLUDED.nombre_contribuyente,
                situacion = EXCLUDED.situacion,
                oficio_definitivo_sat = EXCLUDED.oficio_definitivo_sat,
                fecha_definitivo_sat = EXCLUDED.fecha_definitivo_sat;
        """
        
        bloque_registros = []
        conteo_exito = 0
        
        for index, fila in enumerate(lector_lineas):
            if index < 3: 
                continue # Omitimos las líneas informativas de cabecera del SAT
            
            if len(fila) >= 4:
                try:
                    rfc_limpio = str(fila[1]).strip().upper()
                    if len(rfc_limpio) < 12 or len(rfc_limpio) > 13: 
                        continue
                    
                    consecutivo_crudo = str(fila[0]).strip()
                    consecutivo = int(consecutivo_crudo) if consecutivo_crudo.isdigit() else None
                    
                    # 📐 REPARACIÓN REINA 3: Recortamos rigurosamente los tamaños de strings
                    # para exterminar el error de truncado relacional (character varying 22001)
                    razon_social = str(fila[2]).strip()[:255]
                    situacion_sat = str(fila[3]).strip()[:100]
                    
                    oficio_def = str(fila[12]).strip() if len(fila) > 12 and fila[12] else 'N/A'
                    fecha_def = str(fila[13]).strip() if len(fila) > 13 and fila[13] else 'N/A'
                    
                    oficio_def = oficio_def[:200]
                    fecha_def = fecha_def[:100]

                    bloque_registros.append((
                        consecutivo, rfc_limpio, razon_social, situacion_sat, oficio_def, fecha_def
                    ))

                    # Inyección elástica controlada en lotes de 1,500 registros
                    if len(bloque_registros) >= 1500:
                        try:
                            cursor.executemany(query_upsert_bulk, bloque_registros)
                            conteo_exito += len(bloque_registros)
                            conn.commit()
                        except Exception as inner_e:
                            print(f"⚠️ Alerta: Lote rechazado por Postgres. Limpiando canal: {str(inner_e)}")
                            conn.rollback() # Limpia la tubería TCP relacional si algo colapsa
                        bloque_registros = []
                        
                except Exception:
                    continue

        # Volcado de las filas huérfanas residuales al final del libro de Excel
        if bloque_registros:
            try:
                cursor.executemany(query_upsert_bulk, bloque_registros)
                conteo_exito += len(bloque_registros)
                conn.commit()
            except Exception as last_e:
                print(f"⚠️ Fallo en bloque residual: {str(last_e)}")
                conn.rollback()

        cursor.close()
        conn.close()
        print(f"💾 Éxito Absoluto: {conteo_exito} empresas indexadas en la lista negra relacional.")

        # =========================================================================
        # 🚀 REPARACIÓN REINA: EXTRACCIÓN DINÁMICA MULTI-TENANT (SINO ESTÁTICO)
        # Extraemos el tenant_id real analizando la ruta (Object Key) del archivo en S3
        # Ejemplo de ruta: "notificaciones/bufete-veritas-dev-1234/Listado_completo_69-B.csv"
        # =========================================================================
        try:
            print("🔔 Insertando alerta de auditoría de Listas Negras en el búnker NoSQL...")
            partes_ruta = object_key.split('/')
            
            # Paracaídas: Si la ruta tiene carpetas, el segundo nodo es el Tenant real.
            # Si viene suelto en la raíz, usamos tu fallback contractual de desarrollo.
            tenant_dinamico = partes_ruta[1] if len(partes_ruta) > 2 else "bufete-veritas-uuid-1111"
            
            print(f"🎯 Partición Multi-Tenant localizada con éxito: [{tenant_dinamico}]")
            
            dynamodb_notif = boto3.resource('dynamodb')
            tabla_notif_name = os.environ.get('NOTIFICACIONES_TABLE', "veritas-control-notificaciones-dev")
            table_notif = dynamodb_notif.Table(tabla_notif_name)
            
            fecha_actual_unix = int(datetime.utcnow().timestamp())
            ttl_10_dias = fecha_actual_unix + (10 * 24 * 60 * 60)
            id_alerta = f"NOTIF-69B-{str(uuid.uuid4())[:8].upper()}"

            table_notif.put_item(
                Item={
                    'tenant_id': tenant_dinamico,       # 🎯 Sintonizado al Tenant real de la sesión
                    'notificacion_id': id_alerta,
                    'tipo': 'SISTEMA',
                    'titulo': '🛡️ Validación de Artículo 69-B:',
                    'descripcion': f"Se completó el cruce y la actualización de {conteo_exito} registros de la lista negra oficial del SAT de forma exitosa.",
                    'creado_el': datetime.utcnow().isoformat() + "Z",
                    'leido': False,
                    'fecha_expiracion': ttl_10_dias
                }
            )
            print(f"✅ Alerta de auditoría sembrada exitosamente para el Tenant [{tenant_dinamico}].")
        except Exception as e_notif:
            print(f"⚠️ Alerta: Error sembrando push de listas negras: {str(e_notif)}")

        return {"success": True, "registros_sincronizados": conteo_exito}
        
    except Exception as e:
        print(f"❌ Error crítico general en base de datos: {str(e)}")
        return {"success": False, "error": str(e)}
