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
        port=int(os.environ.get('DB_PORT', 5432))
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
        print("🔍 Ejecutando cruce forense frente a la lista negra del SAT Art. 69-B...")
        authorizer = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        tenant_id = authorizer.get('custom:tenant_id')

        if not tenant_id:
            return {'statusCode': 401, 'headers': headers, 'body': json.dumps({'error': 'Firma multi-tenant inválida.'})}

        conn = obtener_conexion_db()
        cursor = conn.cursor()

        query_forense = """
            SELECT DISTINCT 
                f.rfc_receptor, 
                f.nombre_receptor,
                COALESCE(l.situacion, 'LOCALIZADO SIN OBSERVACIONES') as situacion_sat,
                COALESCE(l.oficio_definitivo_sat, 'N/A') as oficio_sat,
                COALESCE(l.fecha_definitivo_sat, 'N/A') as fecha_sat
            FROM facturas_sat f
            LEFT JOIN lista_negra_sat l ON f.rfc_receptor = l.rfc
            WHERE f.tenant_id = %s 
              AND f.rfc_receptor IS NOT NULL 
              AND f.rfc_receptor != ''
            ORDER BY f.nombre_receptor ASC;
        """
        
        cursor.execute(query_forense, (tenant_id,))
        filas = cursor.fetchall()
        
        auditoria_clientes = []
        for rfc, nombre, situacion, oficio, fecha in filas:
            auditoria_clientes.append({
                "rfc": str(rfc).strip().upper(),
                "nombre": str(nombre).strip() if nombre else str(rfc).strip(),
                "situacion_sat": str(situacion).strip().upper(),
                "oficio_sat": str(oficio).strip(),
                "fecha_sat": str(fecha).strip()
            })

        cursor.close()
        print(f"🎉 Éxito: {len(auditoria_clientes)} clientes auditados de forma pericial.")

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'count': len(auditoria_clientes),
                'reporte_auditoria': auditoria_clientes
            }, ensure_ascii=False)
        }
    except Exception as e:
        print(f"❌ Error en cruce pericial 69-B: {str(e)}")
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
