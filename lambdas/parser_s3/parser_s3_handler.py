# backend/lambdas/finanzas_dashboard/parser_s3_handler.py
import io
import json
import math
import boto3
import pandas as pd

s3_client = boto3.client('s3')

def handler(event, context):
    try:
        print("📊 Microservicio Parser v6 activado. Limpiando tipos de datos mezclados del SAT...")
        detail = event.get('detail', {})
        bucket_name = detail.get('bucket', {}).get('name') or event.get('bucket_name')
        object_key = detail.get('object', {}).get('key') or event.get('object_key')

        tenant_id = object_key.split('/')[0]

        objeto_s3 = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        excel_bytes = objeto_s3['Body'].read()

        # Usamos el separador de punto y coma exacto revelado en tu muestra
        if object_key.lower().endswith('.csv'):
            df = pd.read_csv(
                io.StringIO(excel_bytes.decode('latin-1', errors='ignore')), 
                sep=';', 
                engine='python', 
                on_bad_lines='skip'
            )
        else:
            df = pd.read_excel(io.BytesIO(excel_bytes))

        # Normalizamos todas las cabeceras a minúsculas para evitar desalineaciones
        df.columns = df.columns.str.strip().str.lower()
        
        # Conversión inicial a diccionarios crudos de Python
        facturas_crudas = df.to_dict(orient='records')

        # =========================================================================
        # 🚀 PURIFICACIÓN TOTAL NATIVA EN RAM (Destrucción absoluta de NaNs)
        # =========================================================================
        facturas_json = []
        for factura in facturas_crudas:
            factura_limpia = {}
            for clave, valor in factura.items():
                # Capturamos flotantes NaN e infinitos provocados por las celdas vacías del SAT (ej. Pago ;;)
                if isinstance(valor, float) and (math.isnan(valor) or math.isinf(valor)):
                    factura_limpia[clave] = None
                elif pd.isna(valor) or valor is pd.NA:
                    factura_limpia[clave] = None
                else:
                    factura_limpia[clave] = valor
            facturas_json.append(factura_limpia)

        print(f"🎉 Éxito absoluto: Arreglo sanitizado libre de NaNs con {len(facturas_json)} objetos JSON estándar.")

        # Este payload de texto plano es 100% compatible con el plano de control de AWS Step Functions
        return {
            "tenant_id": tenant_id,
            "facturas": facturas_json
        }
    except Exception as e:
        print(f"🛑 Error fatal en el Parser S3: {str(e)}")
        raise e
