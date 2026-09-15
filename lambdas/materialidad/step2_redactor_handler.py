# =========================================================================
# MICROSERVICIO CORREGIDO: DESPACHADOR MULTIDOCUMENTO POR SECCIÓN SAT
# RUTA EN MAC: lambdas/materialidad/step2_redactor_handler.py
# =========================================================================
import os
import json
import boto3
from concurrent.futures import ThreadPoolExecutor

bedrock_client = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb')

# =========================================================================
# 🏭 MAPEO CORE DE INFRAESTRUCTURA: LAS 4 SECCIONES DEL CHECKLIST REAL
# Vincula qué IDs de documentos deben nacer en cada sección del Front
# =========================================================================
MAPEO_DOCUMENTOS_POR_SECCION = {
    "01_LEGAL_Y_CONSTITUTIVO": [
        "CONTRATO_PRESTACION_SERVICIOS",
        "ACTA_CONSTITUTIVA_RESPALDO",
        "IDENTIFICACION_REPRESENTANTE_LEGAL"
    ],
    "02_CUMPLIMIENTO_FISCAL": [
        "DICTAMEN_OPINION_32D",
        "CONSTANCIA_SITUACION_FISCAL_CEDULA"
    ],
    "03_EVIDENCIA_MATERIALIDAD": [
        "BITACORA_CONTROL_ASISTENCIA",
        "MEMORIA_FOTOGRAFICA_GEOLOCALIZADA"
    ],
    "04_COMPROBACION_FINANCIERA": [
        "INFORME_FLUJO_BANCARIO",
        "CONCILIACION_XML_COMPROBANTES"
    ]
}

def recuperar_y_completar_prompt(doc_id, nombre_cliente, rfc_cliente, ano_fiscal, conceptos_sat):
    nombre_tabla_prompts = os.environ.get('PROMPTS_TABLE', 'veritas-control-prompts-catalog-dev')
    table = dynamodb.Table(nombre_tabla_prompts)
    try:
        response = table.get_item(Key={'id_documento': doc_id})
        item = response.get('Item')
        if not item:
            print(f"⚠️ Prompt [{doc_id}] no sembrado en DynamoDB. Creando prompt genérico emergente...")
            prompt_base = "Redacta el documento formal {id_documento} para {nombre_cliente} ({rfc_cliente}) sobre {conceptos_sat} del año {ano_fiscal}."
            folder_seccion = "01_LEGAL_Y_CONSTITUTIVO"
        else:
            prompt_base = item.get('prompt_base_markdown', '')
            folder_seccion = item.get('folder_seccion', '01_LEGAL_Y_CONSTITUTIVO')

        prompt_finalizado = prompt_base.format(
            nombre_cliente=nombre_cliente, rfc_cliente=rfc_cliente, ano_fiscal=ano_fiscal, conceptos_sat=conceptos_sat
        )
        return prompt_finalizado, folder_seccion
    except Exception as e:
        print(f"❌ Error en lectura NoSQL para {doc_id}: {str(e)}")
        return None, "01_LEGAL_Y_CONSTITUTIVO"

def ejecutar_invocacion_bedrock_hilo(doc_id, nombre_cliente, rfc_cliente, ano_fiscal, conceptos_sat):
    prompt_inyectado, folder_sat = recuperar_y_completar_prompt(doc_id, nombre_cliente, rfc_cliente, ano_fiscal, conceptos_sat)
    if not prompt_inyectado:
        return None

    body_request = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4000,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt_inyectado}]
    })

    try:
        model_id_real = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
        response = bedrock_client.invoke_model(
            modelId=model_id_real, contentType="application/json", accept="application/json", body=body_request
        )
        response_body = json.loads(response.get('body').read())
        
        lista_contenido = response_body.get('content', [])
        texto_ia_markdown = lista_contenido[0].get('text', '').replace("```html", "").replace("```", "").strip()
        
        return {
            "id_documento": doc_id,
            "nombre_archivo": f"{doc_id}_{ano_fiscal}.pdf",
            "folder_seccion": folder_sat,
            "prosa_completa_ia": texto_ia_markdown
        }
    except Exception as e:
        print(f"❌ Error en ráfaga Bedrock para {doc_id}: {str(e)}")
        return None

def handler(event, context):
    print("🤖 Paso 2 Activo: Evaluando Alcance Dinámico Multi-Documento...")
    
    tipo_peticion = event.get('tipo_peticion', 'GENERAR_TODAS')  
    seccion_target = event.get('seccion_target', '01_LEGAL_Y_CONSTITUTIVO')            
    archivo_target = event.get('archivo_target', '')            
    
    nombre_cliente = event.get('nombre_cliente', 'ANTONIO IGNACIO CERVANTES REBOLLO')
    rfc_cliente = event.get('rfc_cliente', 'CERA921023NN6')
    ano_fiscal = event.get('ano_fiscal', '2026')
    conceptos_sat = event.get('string_catalogo_ia', 'Servicios profesionales integrales de consultoría')

    # =========================================================================
    # 🚀 LA MEJORA MAESTRA: DETERMINACIÓN ELÁSTICA DE DOCUMENTOS DEL LOTE
    # Rompe el cuello de botella absorbiendo arrays enteros por sección del Front
    # =========================================================================
    archivos_por_procesar = []
    
    if tipo_peticion == 'GENERAR_TODAS':
        # Succiona absolutamente todos los archivos de las 4 secciones de golpe
        for lista_docs in MAPEO_DOCUMENTOS_POR_SECCION.values():
            archivos_por_procesar.extend(lista_docs)
            
    elif tipo_peticion == 'UNICA_SECCION':
        # 🎯 LA REPARACIÓN REINA: Extrae el array completo de los 3 documentos de esa sección
        archivos_por_procesar = MAPEO_DOCUMENTOS_POR_SECCION.get(seccion_target, [])
        
    elif tipo_peticion == 'UNICO_ARCHIVO':
        archivos_por_procesar = [archivo_target] if archivo_target else ["CONTRATO_PRESTACION_SERVICIOS"]

    print(f"🔎 Lote Determinado: Se enviarán en paralelo [{len(archivos_por_procesar)}] solicitudes a Bedrock.")
    resultados_redaccion_ia = []

    # Ejecución multihilo simultánea real de la lista de documentos
    with ThreadPoolExecutor(max_workers=max(1, len(archivos_por_procesar))) as executor:
        futuros = [
            executor.submit(ejecutar_invocacion_bedrock_hilo, doc_id, nombre_cliente, rfc_cliente, ano_fiscal, conceptos_sat)
            for doc_id in archivos_por_procesar
        ]
        for futuro in futuros:
            res = futuro.result()
            if res:
                resultados_redaccion_ia.append(res)

    event['archivos_redactados_ia'] = resultados_redaccion_ia
    return event
