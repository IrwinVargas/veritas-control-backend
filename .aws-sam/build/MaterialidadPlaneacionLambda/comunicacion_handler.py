def handler(event, context):
    print("⚡ Microservicio Comunicación activado asíncronamente por la Step Function.")
    return {"status": "COMPLETO", "s3_key": f"{event.get('tenant_id')}/{event.get('rfc_cliente')}/comunicacion_empresarial.pdf"}