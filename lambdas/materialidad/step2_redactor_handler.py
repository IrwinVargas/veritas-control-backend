# =========================================================================
# MICROSERVICIO FINAL: REDACTOR DE CONTRATOS SOLEMNES COMPLETOS (DESDE PRIMERO)
# RUTA EN MAC: lambdas/materialidad/step2_redactor_handler.py
# =========================================================================
import os
import json
import boto3

bedrock_client = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

DICCIONARIO_ESPECIALIDAD_SAT = {
    "FINANCIERA_Y_LEGAL": {
        "titulo_contrato": "CONTRATO DE PRESTACIÓN DE SERVICIOS DE CONSULTORÍA INTEGRAL, AUDITORÍA Y GESTIÓN JURÍDICA",
        "entregables_obligatorios": [
            "Papeles de trabajo mensuales de conciliación contable-fiscal en formatos indexados (.xlsx)",
            "Dictámenes y estados financieros intermedios firmados digitalmente por el Contador Público",
            "Bitácoras de consultoría en negocios con desglose de horas-hombre invertidas y entregables lógicos",
            "Minutas solemnes de juntas de consejo operativas, asambleas y reportes de gestoría jurídica avanzada"
        ],
        "enfoque_sustancia": "La prestación de servicios intelectuales de alta especialidad, asesorías contables, auditorías financieras preventivas, consultorías de negocios y gestorías jurídicas corporativas."
    },
    "DESARROLLO_TECNOLOGICO": {
        "titulo_contrato": "CONTRATO DE PRESTACIÓN DE SERVICIOS DE DESARROLLO TECNOLÓGICO, INGENIERÍA DE SOFTWARE Y ARQUITECTURA CLOUD",
        "entregables_obligatorios": [
            "Logs de repositorio Git (control de commits, ramas y fusiones de código fuente)",
            "Diagramas vectoriales de Arquitectura Cloud (AWS/Azure) firmados por el líder técnico",
            "Reportes de pruebas automatizadas QA, UAT y ambientes de staging pre-despliegue",
            "Minutas técnicas de metodologías ágiles (Sprints, Daily Standups) con el equipo asignado"
        ],
        "enfoque_sustancia": "El diseño de arquitectura de software, autoría intelectual de código fuente, despliegue físico de infraestructura elástica en la nube y consultoría de ingeniería tecnológica."
    }
}

def handler(event, context):
    print("🤖 Paso 2 Activo: Invocando la redacción formal de Claude 4.5 en Bedrock...")
    
    nombre_cliente = event.get('nombre_cliente', 'ANTONIO IGNACIO CERVANTES REBOLLO')
    rfc_cliente = event.get('rfc_cliente', 'CERA921023NN6')
    ano_fiscal = event.get('ano_fiscal', '2026')
    
    # 🚀 REPARACIÓN REINA 1: CAPTURA DINÁMICA DEL CONTRATO DESDE EL FRONT-END
    # Jala el string exacto de la carpeta donde el Socio dio clic ('FINANCIERA_Y_LEGAL' o 'DESARROLLO_TECNOLOGICO')
    contrato_tipo = event.get('contrato', 'FINANCIERA_Y_LEGAL')
    if contrato_tipo not in DICCIONARIO_ESPECIALIDAD_SAT:
        contrato_tipo = "FINANCIERA_Y_LEGAL"

    especialidad = DICCIONARIO_ESPECIALIDAD_SAT[contrato_tipo]
    entregables_str = "\n- ".join(especialidad["entregables_obligatorios"])

    # PROMPT FORENSE RE-CALIBRADO PARA ELIMINAR EL "SEGUNDO" MOCHO Y EDITAR CONTRATOS COMPLETOS
    prompt_forense = f"""
    Actúa como un Perito Fiscal Mexicano de Élite y un Abogado Defensor experto en contratos solemnes inatacables ante el SAT para la firma ROUCHERS.
    Redacta un CONTRATO FORMAL DE PRESTACIÓN DE SERVICIOS PROFESIONALES completo, denso y exhaustivo.
    
    DATOS DEL CONTRATO:
    - Título Oficial: {especialidad["titulo_contrato"]}
    - Prestador: ROUCHERS (RFC: ROU2203162G8)
    - Cliente Beneficiario: {nombre_cliente} (RFC: {rfc_cliente})
    - Ejercicio de Ejecución: {ano_fiscal}
    
    🎯 INFRAESTRUCTURA Y SUSTANCIA COMERCIAL A CITAR:
    {especialidad["enfoque_sustancia"]}
    
    📋 CLAUSULADO DE ENTREGABLES OBLIGATORIOS CONTEMPLADOS QUE DEBES DEFENDER Y DESGLOSAR:
    - {entregables_str}
    
    ESTRUCTURA DE REDACCIÓN (ESTRICTA):
    1. Inicia obligatoriamente desde el 'PRIMERO'. Diseña un clausulado formal que contenga:
       - <b>PRIMERO. OBJETO DEL CONTRATO.</b> (Detalla densamente el alcance de: {especialidad["enfoque_sustancia"]})
       - <b>SEGUNDO. INFRAESTRUCTURA Y CAPACIDAD OPERATIVA.</b> (Argumenta que ROUCHERS cuenta con los recursos humanos directos, activos y herramientas para ejecutar el servicio, blindando al cliente contra el 69-B del CFF)
       - <b>TERCERO. MATERIALIDAD PROBATORIA Y CADENA DE CUSTODIA.</b> (Desglosa mecánicamente cómo se supervisarán, entregarán y custodiarán de forma mensual los entregables del catálogo: {especialidad["entregables_obligatorios"]})
       - <b>CUARTO. CONTRAPRESTACIÓN, FLUJO FINANCIERO Y CONFIDENCIALIDAD.</b> (Especifica el flujo de pagos por transferencias bancarias y el blindaje de secreto profesional)
    2. Debe ser extenso, formal, de alta prosa jurídica corporativa mexicana. Genera párrafos largos y robustos para cada cláusula.
    3. Cita expresamente el nombre de ROUCHERS y de {nombre_cliente}.
    
    Genera únicamente el cuerpo de las cláusulas justificadas, usando etiquetas HTML básicas como <b> o <br/> para separar los títulos. No incluyas marcas de código markdown (```html), introducciones ni saludos de cortesía.
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
        print(f"📡 Transmitiendo Prompt hacia Claude 4.5 en Bedrock: {model_id_real}")
        
        response = bedrock_client.invoke_model(
            modelId=model_id_real,
            contentType="application/json",
            accept="application/json",
            body=body_request
        )
        
        response_body = json.loads(response.get('body').read())
        texto_pericial_generado = response_body['content']['text']
        
        print("✅ Contrato solemne completo redactado con éxito por Claude 4.5 en Bedrock.")
        event['texto_pericial'] = texto_pericial_generado
        
    except Exception as e:
        print(f"❌ Error crítico invocando Bedrock Real: {str(e)}")
        event['texto_pericial'] = None 

    return event
