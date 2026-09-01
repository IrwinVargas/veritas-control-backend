import os
import boto3

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    try:
        print("🏁 Orquestador completado. Sellando estatus global de Reconstrucción...")
        tenant_id = "bufete-veritas" 
        rfc_cliente = "ROU2203162G8"
        
        hash_key = f"{tenant_id}#{rfc_cliente}"
        table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE'))
        
        # Actualización quirúrgica del estatus de la aduana general
        table.update_item(
            Key={'tenant_rfc': hash_key},
            UpdateExpression="SET estatus_expediente = :est",
            ExpressionAttributeValues={':est': 'COMPLETO'}
        )
        return {"success": True}
    except Exception as e:
        print(f"❌ Error en consolidador final: {str(e)}")
        raise e
