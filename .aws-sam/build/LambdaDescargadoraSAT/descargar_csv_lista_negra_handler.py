import os
import requests
import boto3

s3_client = boto3.client('s3')

def handler(event, context):
    try:
        url_csv_sat = os.environ.get('URL_CSV_SAT')
        bucket_destino = os.environ.get('BUCKET_DESTINO') # ej. sat-listas-negras-temporal
        nombre_archivo = "Listado_completo_69-B.csv"

        headers_peticion = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        print("Descargando desde el SAT y transmitiendo directo a S3...")
        
        # Conectamos con el SAT con salida a internet libre
        with requests.get(url_csv_sat, headers=headers_peticion, stream=True, timeout=60) as respuesta:
            respuesta.raise_for_status()
            
            # Subimos el flujo directamente a S3 sin guardarlo completo en la RAM de la Lambda
            s3_client.upload_fileobj(respuesta.raw, bucket_destino, nombre_archivo)
            
        print("¡Archivo depositado con éxito en S3!")
        return {"success": True, "message": "Archivo listo en S3"}
        
    except Exception as e:
        print(f"❌ Error descargando del SAT: {str(e)}")
        return {"success": False, "error": str(e)}
