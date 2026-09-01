import os
import io
import csv
import boto3
import pg8000

s3_client = boto3.client('s3')

def handler(event, context):
    try:
        # Obtenemos los datos del archivo desde el evento de S3
        record = event['Records'][0]
        bucket_name = record['s3']['bucket']['name']
        object_key = record['s3']['object']['key']
        
        print(f"Detectado nuevo archivo en S3: {object_key}. Procesando...")

        # Obtenemos el stream de lectura del archivo en S3
        objeto_s3 = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        
        # Procesamos línea por línea decodificando desde S3 de forma eficiente
        lineas_flujo = io.TextIOWrapper(objeto_s3['Body'], encoding='latin-1')
        lector_lineas = csv.reader(lineas_flujo, delimiter=',')
        
        print("Conectando a la DB... ")

        # Conexión local/privada a la base de datos PostgreSQL dentro de la VPC
        conn = pg8000.connect(
            host=os.environ.get('DB_HOST'),
            database=os.environ.get('DB_NAME'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            port=int(os.environ.get('DB_PORT', 5432)),
            timeout=15
        )
        cursor = conn.cursor()

        print("Ejecutando script... ")
        print("Vaciando tabla destino en la base de datos...")
        cursor.execute("TRUNCATE TABLE lista_negra_sat;")

        query_bulk_insert = """
            INSERT INTO lista_negra_sat (
                numero_consecutivo, rfc, nombre_contribuyente, situacion, 
                oficio_definitivo_sat, fecha_definitivo_sat
            ) VALUES (%s, %s, %s, %s, %s, %s);
        """
        
        bloque_registros = []
        conteo_exito = 0
        
        for index, fila in enumerate(lector_lineas):
            if index < 3: continue 
            
            if len(fila) >= 4:
                try:
                    rfc_limpio = str(fila[1]).strip().upper()
                    if len(rfc_limpio) < 12 or len(rfc_limpio) > 13: continue
                    
                    consecutivo_crudo = str(fila[0]).strip()
                    consecutivo = int(consecutivo_crudo) if consecutivo_crudo.isdigit() else None
                    
                    razon_social = str(fila[2]).strip()
                    situacion_sat = str(fila[3]).strip()
                    
                    oficio_def = str(fila[12]).strip() if len(fila) > 12 and fila[12] else 'N/A'
                    fecha_def = str(fila[13]).strip() if len(fila) > 13 and fila[13] else 'N/A'

                    bloque_registros.append((
                        consecutivo, rfc_limpio, razon_social, situacion_sat, oficio_def, fecha_def
                    ))
                    conteo_exito += 1

                    if len(bloque_registros) >= 1500:
                        cursor.executemany(query_bulk_insert, bloque_registros)
                        bloque_registros = []
                except Exception:
                    continue

        if bloque_registros:
            cursor.executemany(query_bulk_insert, bloque_registros)

        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Éxito Absoluto: Se integraron {conteo_exito} empresas a la BD.")
        return {"success": True, "registros_sincronizados": conteo_exito}
        
    except Exception as e:
        print(f"❌ Error crítico en base de datos: {str(e)}")
        return {"success": False, "error": str(e)}
