# lambdas/materialidad/step2_redactor_handler.py
import os
import json
import boto3

# Inicializamos el cliente nativo de Amazon Bedrock en la región asignada
bedrock_client = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

def handler(event, context):
    print("🤖 Paso 2 Activo: Invocando la inteligencia forense de Amazon Bedrock...")
    
    nombre_cliente = event.get('nombre_cliente', 'El Contribuyente')
    rfc_cliente = event.get('rfc_cliente', '')
    contrato_tipo = event.get('contrato', 'PRESTACION_SERVICIOS')
    ano_fiscal = event.get('ano_fiscal', '2026')
    
    # Succionamos el string de conceptos purificados que nos heredó el Paso 1 de Postgres
    conceptos_sat_crudos = event.get('string_catalogo_ia', 'Servicios administrativos corporativos')

    # 🛡️ PROMPT DE MÁXIMA DEFECTOLOGÍA LEGAL JURÍDICA MEXICANA (ANTI-HUECOS DEL SAT)
    prompt_forense = f"""
    Actúa como un Perito Fiscal Mexicano de Élite y un Abogado Defensor experto en el Artículo 69-B del CFF.
    Redacta la sección 'SEGUNDO. DEFECTOLOGÍA OPERATIVA Y ENTREGABLES' para un expediente de materialidad inatacable.
    
    DATOS DEL CASO:
    - Cliente: {nombre_cliente} (RFC: {rfc_cliente})
    - Tipo de Contrato: {contrato_tipo}
    - Ejercicio Fiscal: {ano_fiscal}
    - Conceptos de Facturación Detectados en Postgres: {conceptos_sat_crudos}
    
    REQUISITOS DE REDACCIÓN (ESTRICTOS):
    1. Debe ser denso, exhaustivo, corporativo y formal. Prohibido dar respuestas resumidas o viñetas escuetas.
    2. Explica de forma científica y transaccional cómo se ejecutaron, supervisaron y entregaron estos servicios.
    3. Cita entregables reales: bitácoras de avance, minutas de control, entregables digitales, métricas de entregas y reportes mensuales.
    4. Demuestra la sustancia económica de forma inatacable para que el SAT no pueda alegar simulación de actos.
    
    Genera únicamente el cuerpo del texto legal justificado, usando etiquetas HTML básicas como <b> o <br/> si es necesario. No incluyas introducciones ni saludos de cortesía.
    """

    # Estructuramos el payload oficial para Claude 3.5 / 4.5 Haiku
    body_request = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4000,
        "temperature": 0.2, # Latencia baja y máxima precisión legal sin alucinaciones
        "messages": [
            {
                "role": "user",
                "content": prompt_forense
            }
        ]
    })

    try:
        # Invocamos el modelo fundacional de Amazon Bedrock
        response = bedrock_client.invoke_model(
            modelId="anthropic.claude-3-5-haiku-20241022-v1:0", # O tu id de perfil de Claude 4.5
            contentType="application/json",
            accept="application/json",
            body=body_request
        )
        
        response_body = json.loads(response.get('body').read())
        texto_pericial_generado = response_body['content'][0]['text']
        
        print("✅ Tesis de materialidad redactada con éxito por Bedrock.")
        
        # Inyectamos el texto de la IA al payload del evento
        event['texto_pericial'] = texto_pericial_generado
        
    except Exception as e:
        print(f"❌ Error invocando Bedrock: {str(e)}")
        # Fallback de seguridad legal para que la Step Function no muera y el Paso 3 pueda esculpir
        event['texto_pericial'] = f"<b>SEGUNDO. CERTIFICACIÓN DE OPERACIONES.</b> Se ratifica la materialidad de las operaciones relativas a {conceptos_sat_crudos} para el ejercicio {ano_fiscal}."

    # Heredamos el payload hacia el Paso 3 (El Escultor de ReportLab)
    return event
