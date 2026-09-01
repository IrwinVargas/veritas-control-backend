import os
import json
import pg8000

_db_connection = None

def obtener_conexion_db():
    global _db_connection
    if _db_connection and _db_connection._sock is not None:
        return _db_connection
        
    _db_connection = pg8000.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        port=int(os.environ.get('DB_PORT', 5432)),
        timeout=10
    )
    return _db_connection

def handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }

    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'message': 'OK'})}

    try:
        print("👥 Buscando catálogo único de clientes multi-tenant...")
        
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        tenant_id = authorizer.get('custom:tenant_id')

        if not tenant_id:
            return {'statusCode': 401, 'headers': headers, 'body': json.dumps({'error': 'Firma multi-tenant no localizada.'})}

        conn = obtener_conexion_db()
        cursor = conn.cursor()

        query_clientes = """
            SELECT DISTINCT rfc_receptor, nombre_receptor
            FROM facturas_sat
            WHERE tenant_id = %s 
              AND rfc_receptor IS NOT NULL 
              AND rfc_receptor != ''
              AND tipo_de_comprobante = 'I'
            ORDER BY nombre_receptor ASC;
        """
        
        cursor.execute(query_clientes, (tenant_id,))
        filas = cursor.fetchall()
        
        lista_clientes = []
        for rfc, nombre in filas:
            lista_clientes.append({
                "rfc": str(rfc).strip().upper(),
                "nombre": str(nombre).strip() if nombre else str(rfc).strip().upper()
            })

        cursor.close()
        print(f"🎉 Éxito: Se localizaron {len(lista_clientes)} clientes únicos para el bufete.")

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'count': len(lista_clientes),
                'clientes': lista_clientes
            }, ensure_ascii=False)
        }
    except Exception as e:
        print(f"❌ Error crítico en buscador de clientes: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
