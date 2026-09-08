import os
import io
import csv
import boto3
import pg8000

s3_client = boto3.client('s3')

def handler(event, context):
    try:
        # Obtenemos las coordenadas del archivo depositado por tu Lambda 1 en S3
        record = event['Records'][0]
        bucket_name = record['s3']['bucket']['name']
        object_key = record['s3']['object']['key']
        
        print(f"📡 Detectado nuevo listado del SAT en S3: {object_key}. Iniciando inyección forense...")

        # Consumimos el objeto de forma eficiente como un flujo binario directo
        objeto_s3 = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        
        # Procesamos línea por línea decodificando desde S3 en latin-1 (Estándar SAT)
        lineas_flujo = io.TextIOWrapper(objeto_s3['Body'], encoding='latin-1')
        lector_lineas = csv.reader(lineas_flujo, delimiter=',')
        
        print("🔗 Abriendo socket TCP privado con la base de datos PostgreSQL dentro de la VPC...")
        conn = pg8000.connect(
            host=os.environ.get('DB_HOST'),
            database=os.environ.get('DB_NAME'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            port=int(os.environ.get('DB_PORT', 5432)),
            timeout=15
        )
        cursor = conn.cursor()

        print("🧹 Limpiando histórico: Vaciando la tabla lista_negra_sat para indexación fresca...")
        cursor.execute("TRUNCATE TABLE lista_negra_sat;")
        conn.commit()
        
        query_bulk_insert = """
            INSERT INTO lista_negra_sat (
                numero_consecutivo, rfc, nombre_contribuyente, situacion, 
                oficio_definitivo_sat, fecha_definitivo_sat
            ) VALUES (%s, %s, %s, %s, %s, %s);
        """
        
        bloque_registros = []
        conteo_exito = 0
        
        for index, fila in enumerate(lector_lineas):
            if index < 3: 
                continue # Omitimos las cabeceras informativas del SAT
            
            if len(fila) >= 4:
                try:
                    rfc_limpio = str(fila[1]).strip().upper()
                    # Paracaídas estricto: Si el RFC está deformado, saltamos la celda para no herir la BD
                    if len(rfc_limpio) < 12 or len(rfc_limpio) > 13: 
                        continue
                    
                    consecutivo_crudo = str(fila[0]).strip()
                    consecutivo = int(consecutivo_crudo) if consecutivo_crudo.isdigit() else None
                    
                    razon_social = str(fila[2]).strip()
                    situacion_sat = str(fila[3]).strip()
                    
                    # 📐 PROTECCIÓN DE LONGITUD DE STRINGS: Recortamos los excedentes del SAT 
                    # para evitar violaciones sintácticas de varchar rígidos en la base de datos
                    oficio_def = str(fila[12]).strip() if len(fila) > 12 and fila[12] else 'N/A'
                    fecha_def = str(fila[13]).strip() if len(fila) > 13 and fila[13] else 'N/A'
                    
                    oficio_def = oficio_def[:200]
                    fecha_def = fecha_def[:100]

                    bloque_registros.append((
                        consecutivo, rfc_limpio, razon_social, situacion_sat, oficio_def, fecha_def
                    ))

                    if len(bloque_registros) >= 1500:
                        try:
                            cursor.executemany(query_bulk_insert, bloque_registros)
                            conteo_exito += len(bloque_registros)
                            conn.commit() # Consolidamos el lote exitoso
                        except Exception as inner_e:
                            # 🚀 LA SOLUCIÓN REINA: Si el lote completo falla por un renglón corrupto,
                            # limpiamos el canal TCP relacional de Postgres para que la transacción no quede muerta
                            print(f"⚠️ Alerta: Lote masivo rechazado por Postgres. Limpiando canal: {str(inner_e)}")
                            conn.rollback() 
                        bloque_registros = []
                        
                except Exception:
                    continue

        # Volcado de las filas huérfanas residuales que se quedaron al final del archivo
        if bloque_registros:
            try:
                cursor.executemany(query_bulk_insert, bloque_registros)
                conteo_exito += len(bloque_registros)
                conn.commit()
            except Exception as last_e:
                print(f"⚠️ Fallo en bloque residual: {str(last_e)}")
                conn.rollback()

        cursor.close()
        conn.close()
        
        print(f"💾 Éxito Absoluto: Sincronización finalizada. {conteo_exito} empresas indexadas en la lista negra relacional.")
        return {"success": True, "registros_sincronizados": conteo_exito}
        
    except Exception as e:
        print(f"❌ Error crítico en base de datos de listas negras: {str(e)}")
        return {"success": False, "error": str(e)}