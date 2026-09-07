import json
import boto3

bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

def handler(event, context):
    print("🧠 Paso 2 Activo: Modelado de Tesis del SAT en Bedrock con Internet Público...")
    
    nombre_cliente = event.get('nombre_cliente')
    tipo_flujo = event.get('tipo_flujo')
    contrato = event.get('contrato')
    ano_fiscal = event.get('ano_fiscal')
    string_catalogo_ia = event.get('string_catalogo_ia')

    # PROMPT PREMIUM DE ALTA FIDELIDAD SIN CARACTERES BASURA (# o *)
    prompt = f"""
    Humano: Actúa como Perito Senior en Compliance y Defensa Fiscal en México. 
    Redacta la INTRODUCCIÓN, DESARROLLO OPERATIVO y JUSTIFICACIÓN de materialidad para {nombre_cliente} bajo el escenario: "{tipo_flujo}" del contrato "{contrato}" para el año {ano_fiscal}.
    Sustenta tus argumentos jurídicos en esta gama real de soluciones tangibles:
    {string_catalogo_ia}
    
    REGLA DE ORO DE DISEÑO: No incluyas notas de autor, comentarios informáticos ni uses caracteres Markdown como almohadillas (#) o asteriscos (*). Usa texto plano formal.
    Asistente:
    """

    body_payload = json.dumps({"anthropic_version": "bedrock-2023-05-31", "max_tokens": 1800, "temperature": 0.1, "messages": [{"role": "user", "content": prompt}]})
    response = bedrock_runtime.invoke_model(body=body_payload, modelId="us.anthropic.claude-haiku-4-5-20251001-v1:0", accept="application/json", contentType="application/json")
    texto_pericial = json.loads(response.get('body').read()).get('content', [{}]).get('text', '').replace('#', '').replace('*', '').strip()

    # Agregamos la redacción al payload y avanzamos al paso final
    event['texto_pericial'] = texto_pericial
    return event
