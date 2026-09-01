import os
import uuid
import json
import pg8000

def handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }

    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        print("Procesando alta manual de cliente prospecto...")
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        tenant_id = authorizer.get('custom:tenant_id')
        bufete_rfc = authorizer.get('custom:bufete_rfc')
        bufete_name = authorizer.get('custom:bufete_name')

        body = json.loads(event.get('body', '{}'))
        rfc = str(body.get('rfc', '')).strip().upper()
        nombre = str(body.get('nombre', '')).strip()
        
        if not tenant_id or not bufete_rfc:
            return {
                'statusCode': 401, 
                'headers': headers, 
                'body': json.dumps({'error': 'Firma de ciberseguridad o RFC del bufete no localizados.'})
            }

        if len(rfc) < 12 or len(rfc) > 13 or not nombre:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'RFC o Razón Social inválidos.'})}
        
        folio_manual_uuid = f"MANUAL-{str(uuid.uuid4()).upper()}"

        conn = pg8000.connect(
            host=os.environ.get('DB_HOST'),
            database=os.environ.get('DB_NAME'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            port=int(os.environ.get('DB_PORT', 5432))
        )
        cursor = conn.cursor()

        query_insert = """
            INSERT INTO facturas_sat (
                tenant_id, rfc_emisor, nombre_emisor, rfc_receptor, nombre_receptor, folio_fiscal_uuid, 
                fecha_hora_timbrado, sub_total, total_iva, total, tipo_de_comprobante
            ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 0.00, 0.00, 0.00, 'I');
        """
        
        cursor.execute(query_insert, (tenant_id, bufete_rfc.upper().strip(), bufete_name, rfc, nombre, folio_manual_uuid))
        conn.commit()
        
        cursor.close()
        conn.close()

        print(f"Cliente manual registrado con éxito: {rfc} - {nombre}")
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'success': True, 'message': 'Cliente registrado exitosamente en el catálogo.'})
        }
    except Exception as e:
        print(f"❌ Error fatal en alta manual de cliente: {str(e)}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
