def handler(event, context):
    print("⚡ Microservicio Evidencias activado asíncronamente por la Step Function.")
    return {"status": "COMPLETO", "s3_key": f"{event.get('tenant_id')}/{event.get('rfc_cliente')}/evidencias_multimedia.pdf"}