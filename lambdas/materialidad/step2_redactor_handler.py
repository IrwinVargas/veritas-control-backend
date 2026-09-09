import os
import json
import boto3

bedrock_client = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

DICCIONARIO_ESPECIALIDAD_SAT = {
    "DESARROLLO_TECNOLOGICO": {
        "entregables_obligatorios": [
            "Logs de repositorio Git (control de commits, ramas y fusiones de código fuente)",
            "Diagramas vectoriales de Arquitectura Cloud (AWS/Azure) firmados por el líder técnico",
            "Reportes de pruebas automatizadas QA, UAT y ambientes de staging pre-despliegue",
            "Minutas técnicas de metodologías ágiles (Sprints, Daily Standups) con el equipo asignado"
        ],
        "enfoque_sustancia": "Demostrar la autoría intelectual, el despliegue físico de la infraestructura en la nube y las horas de desarrollo técnico medibles."
    },
    "LOGISTICA_Y_TRANSPORTE": {
        "entregables_obligatorios": [
            "Complementos Carta Porte timbrados y vinculados al CFDI de traslado oficial",
            "Bitácoras de rastreo satelital GPS con coordenadas, paradas y manifiestos de ruta",
            "Pólizas de seguro de mercancía vigentes y guías de embarque firmadas por el operador",
            "Registros de mantenimiento preventivo de la flotilla vehicular utilizada"
        ],
        "enfoque_sustancia": "Demostrar la trazabilidad física de la mercancía, la legal posesión de los vehículos y la ejecución real del traslado en territorio nacional."
    },
    "REPSE_PERSONAL": {
        "entregables_obligatorios": [
            "Comprobantes de pago de cuotas obrero-patronales IMSS (SUA y emisiones EBA)",
            "Archivos XML y PDF de los recibos de nómina timbrados de los trabajadores asignados",
            "Formatos DC-3 de acreditación de habilidades laborales y registro REPSE vigente",
            "Bitácoras firmadas de entrega de equipo de protección personal (EPP) e insumos"
        ],
        "enfoque_sustancia": "Acreditar plenamente la subordinación, el estricto cumplimiento de las obligaciones de seguridad social y el registro en el padrón de la STPS."
    }
}

def handler(event, context):
    print("🤖 Paso 2 Activo: Invocando la inteligencia forense de Amazon Bedrock...")
    
    nombre_cliente = event.get('nombre_cliente', 'El Contribuyente')
    rfc_cliente = event.get('rfc_cliente', '')
    contrato_tipo = event.get('contrato', 'PRESTACION_SERVICIOS')
    ano_fiscal = event.get('ano_fiscal', '2026')
    
    conceptos_sat_crudos = event.get('string_catalogo_ia', '')
    if not conceptos_sat_crudos and 'step1_output' in event:
        conceptos_sat_crudos = event.get('step1_output', {}).get('string_catalogo_ia', '')
        
    if not conceptos_sat_crudos:
        conceptos_sat_crudos = "Servicios administrativos corporativos y de asesoría fiscal integral"

    especialidad = DICCIONARIO_ESPECIALIDAD_SAT.get(
        contrato_tipo, 
        {
            "entregables_obligatorios": ["Reportes mensuales de actividades", "Minutas de control", "Entregables digitales estándar"],
            "enfoque_sustancia": "Demostrar la ejecución real del servicio mediante entregables lógicos, medibles y trazables."
        }
    )

    entregables_str = "\n- ".join(especialidad["entregables_obligatorios"])

    prompt_forense = f"""
    Actúa como un Perito Fiscal Mexicano de Élite y un Abogado Defensor experto en el Artículo 69-B del CFF.
    Redacta la sección 'SEGUNDO. DEFECTOLOGÍA OPERATIVA Y ENTREGABLES ESPECIALIZADOS' para un expediente de materialidad inatacable.
    
    DATOS DEL CASO:
    - Cliente: {nombre_cliente} (RFC: {rfc_cliente})
    - Tipo de Contrato: {contrato_tipo}
    - Ejercicio Fiscal: {ano_fiscal}
    - Conceptos de Facturación Detectados en Postgres: {conceptos_sat_crudos}
    
    🎯 DIRECTRICES DE SUSTANCIA ESPECÍFICA PARA ESTE SERVICIO:
    {especialidad["enfoque_sustancia"]}
    
    📋 EL CLIENTE YA GENERÓ Y DEBES CITAR, ARGUMENTAR Y DEFENDER LA EXISTENCIA DE LOS SIGUIENTES ARCHIVOS DE ESPECIALIDAD:
    - {entregables_str}
    
    REQUISITOS DE REDACCIÓN (ESTRICTOS):
    1. Debe ser denso, de alta prosa jurídica, formal y exhaustivo. Explica mecánicamente cómo se ejecutaron, supervisaron y custodiaron estos entregables específicos. Genera mínimo 4 párrafos largos de argumentación pericial.
    2. Cita los archivos de especialidad listados arriba, demostrando de forma inatacable que no existe simulación de actos y que la infraestructura técnica/humana del proveedor coincide perfectamente con el volumen del servicio.
    3. Justifica el flujo transaccional de los entregables para cerrar cualquier brecha de duda ante el SAT.
    
    Genera únicamente el cuerpo del texto legal justificado, usando etiquetas HTML básicas como <b> o <br/> si es necesario. No incluyas introducciones ni saludos de cortesía.
    """

    body_request = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4000,
        "temperature": 0.2,
        "messages": [
            {"role": "user", "content": prompt_forense}
        ]
    })

    try:
        model_id_real = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
        
        print(f"📡 Transmitiendo Prompt pericial forense hacia el modelo: {model_id_real}")
        response = bedrock_client.invoke_model(
            modelId=model_id_real,
            contentType="application/json",
            accept="application/json",
            body=body_request
        )
        
        response_body = json.loads(response.get('body').read())
        texto_pericial_generado = response_body['content'][0]['text']
        
        print("✅ Tesis de materialidad especializada redactada con éxito por Claude 4.5 en Bedrock.")
        event['texto_pericial'] = texto_pericial_generado
        
    except Exception as e:
        print(f"❌ Error crítico invocando Bedrock Real: {str(e)}")
        event['texto_pericial'] = None # Forzamos que caiga en el paracaídas extendido del Paso 3

    return event
