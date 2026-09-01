import os
import json
import csv
import io
import requests
import psycopg2
from psycopg2.extras import execute_values

def obtener_conexion_db():
    """Establece comunicación segura con tu clúster de Amazon Aurora Postgres"""
    return psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        port=os.environ.get('DB_PORT', '5432')
    )

def handler(event, context):
    # URL Oficial del SAT para la descarga de la lista completa del 69-B
    URL_LISTA_SAT = "https://sat.gob.mx"
    
    print("Iniciando descarga de la lista negra oficial del SAT (Art. 69-B CFF)...")
    
    try:
        # Descarga del archivo binario desde los servidores del SAT
        response = requests.get(URL_LISTA_SAT, timeout=60)
        if response.status_code != 200:
            raise Exception(f"El servidor del SAT respondió con código de error HTTP: {response.status_code}")
        
        # Decodificación del texto (El SAT suele codificar en 'latin-1' o 'utf-8')
        content_text = response.content.decode('latin-1')
        csv_file = io.StringIO(content_text)
        
        # El archivo del SAT contiene un encabezado en las primeras líneas; lo saltamos con el lector de CSV
        reader = csv.reader(csv_file, delimiter=',')
        
        rfc_data_to_upsert = []
        
        print("🧹 Analizando y depurando renglones del listado...")
        for row in reader:
            # Validamos que el renglón contenga datos y el primer elemento parezca un RFC (longitud de 12 a 13 letras)
            if not row or len(row) < 3:
                continue
            
            rfc = row[1].strip().upper()
            nombre_contribuyente = row[2].strip()
            estatus_sat = row[3].strip() # Presunto, Definitivo, Desvirtuados, Sentencia Favorable
            
            # Micro-validación de seguridad para saltar el renglón de títulos del Excel del SAT
            if rfc == "RFC" or len(rfc) < 12 or len(rfc) > 13:
                continue
                
            rfc_data_to_upsert.append((
                rfc,
                nombre_contribuyente,
                estatus_sat
            ))
            
        print(f"Se depuraron {len(rfc_data_to_upsert)} registros del SAT listos para indexar.")

        # =========================================================================
        # PERSISTENCIA EN DATABASE: INYECCIÓN MASIVA EN POSTGRES
        # =========================================================================
        conn = obtener_conexion_db()
        cursor = conn.cursor()
        
        # Estructura SQL optimizada: Si el RFC ya existía, actualiza su estatus legal al vuelo; si no, lo inserta
        query_upsert = """
            INSERT INTO sat_lista_negra (rfc, razon_social, estatus_legal, ultima_actualizacion)
            VALUES %s
            ON CONFLICT (rfc) 
            DO UPDATE SET 
                estatus_legal = EXCLUDED.estatus_legal,
                razon_social = EXCLUDED.razon_social,
                ultima_actualizacion = CURRENT_TIMESTAMP;
        """
        
        # execute_values realiza la inserción en bloques de alta velocidad (Batch injection)
        execute_values(cursor, query_upsert, rfc_data_to_upsert)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Amazon Aurora Postgres sincronizado e indexado correctamente.")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'success': True, 'records_synced': len(rfc_data_to_upsert)})
        }
        
    except Exception as e:
        print(f"Error crítico en el cron del sincronizador del SAT: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Fallo en la tarea programada: {str(e)}'})
        }
