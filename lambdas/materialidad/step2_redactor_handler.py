# =========================================================================
# MICROSERVICIO FINAL: REDACTOR ASÍNCRONO BASADO EN CATÁLOGO DE PROMPTS NOSQL
# RUTA EN MAC: lambdas/materialidad/step2_redactor_handler.py
# =========================================================================
import os
import json
import boto3
from concurrent.futures import ThreadPoolExecutor

bedrock_client = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb')

# 🚀 FUNCIÓN AISLADA: SUCCIONAL EL PROMPT DE DYNAMODB E INYECTA LOS DATOS EN CALIENTE
def recuperar_y_completar_prompt(doc_id, nombre_cliente, rfc_cliente, ano_fiscal, conceptos_sat):
    nombre_tabla_prompts = os.environ.get('PROMPTS_TABLE', 'veritas-control-prompts-catalog-dev')
    table = dynamodb.Table(nombre_tabla_prompts)
    
    try:
        # Succiona el machote base guardado en la base de conocimientos NoSQL
        response = table.get_item(Key={'id_documento': doc_id})
        item = response.get('Item')
        
        if not item:
            print(f"⚠️ Advertencia: No se encontró el prompt para [{doc_id}] en DynamoDB. Usando fallback noble.")
            prompt_maestro_crudo = "Redacta un documento formal de materialidad para {nombre_cliente} ({rfc_cliente}) sobre {conceptos_sat} año {ano_fiscal}."
            folder_seccion = "01_LEGAL_Y_CONSTITUTIVO"
        else:
            prompt_maestro_crudo = item.get('prompt_base_markdown', '')
            folder_seccion = item.get('folder_seccion', '01_LEGAL_Y_CONSTITUTIVO')

        # 🎯 COMPOSICIÓN DINÁMICA: Rellenamos los casilleros vacíos con la info real del cliente
        prompt_finalizado = prompt_maestro_crudo.format(
            nombre_cliente=nombre_cliente,
            rfc_cliente=rfc_cliente,
            ano_fiscal=ano_fiscal,
            conceptos_sat=conceptos_sat
        )
        
        return prompt_finalizado, folder_seccion
    except Exception as e:
        print(f"❌ Error succionando prompt para {doc_id} de DynamoDB: {str(e)}")
        return None, "01_LEGAL_Y_CONSTITUTIVO"

# HILO CONCURRENTE EN PARALELO PARA INVOCAR A CLAUDE 4.5
def ejecutar_invocacion_bedrock_hilo(doc_id, nombre_cliente, rfc_cliente, ano_fiscal, conceptos_sat):
    # 1. Pedimos el prompt armado de la sección
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
        print(f"📡 Hilo Activo PrivateLink: Transmitiendo a Bedrock para [{doc_id}]...")
        
        response = bedrock_client.invoke_model(
            modelId=model_id_real, contentType="application/json", accept="application/json", body=body_request
        )
        response_body = json.loads(response.get('body').read())
        texto_ia_markdown = response_body['content']['text'].replace("```html", "").replace("```", "").strip()
        
        return {
            "id_documento": doc_id,
            "nombre_archivo": f"{doc_id}_{ano_fiscal}.pdf",
            "folder_seccion": folder_sat,
            "prosa_completa_ia": texto_ia_markdown # Viaja el texto Markdown puro para el Paso 3
        }
    except Exception as e:
        print(f"❌ Error en ráfaga Bedrock para {doc_id}: {str(e)}")
        return None

def handler(event, context):
    print("🤖 Paso 2 Activo: Ejecutando Inyector elástico Multi-Prompt desde DynamoDB NoSQL...")
    
    tipo_peticion = event.get('tipo_peticion', 'GENERAR_TODAS')  
    seccion_target = event.get('seccion_target', '')            
    archivo_target = event.get('archivo_target', '')            
    
    nombre_cliente = event.get('nombre_cliente', 'ANTONIO IGNACIO CERVANTES REBOLLO')
    rfc_cliente = event.get('rfc_cliente', 'CERA921023NN6')
    ano_fiscal = event.get('ano_fiscal', '2026')
    conceptos_sat = event.get('string_catalogo_ia', 'Servicios profesionales integrales corporativos contables')

    # Catálogo elástico de validación de documentos requeridos por la aduana del Front
    # (Esto lo puedes mapear dinámicamente haciendo un scan rápido a tu tabla de prompts en vez de un array estático)
    catálogo_maestro_docs = ["CONTRATO_PRESTACION_SERVICIOS", "DICTAMEN_OPINION_32D", "BITACORA_CONTROL_ASISTENCIA", "INFORME_FLUJO_BANCARIO"]
    
    archivos_por_procesar = []
    if tipo_peticion == 'GENERAR_TODAS':
        archivos_por_procesar = catálogo_maestro_docs
    elif tipo_peticion == 'UNICA_SECCION':
        # Fallback elástico temporal de filtrado por segmento
        archivos_por_procesar = [archivo_target] if archivo_target else [catálogo_maestro_docs[0]]
    elif tipo_peticion == 'UNICO_ARCHIVO':
        archivos_por_procesar = [archivo_target] if archivo_target else ["CONTRATO_PRESTACION_SERVICIOS"]

    resultados_redaccion_ia = []

    # 🚀 EJECUCIÓN MULTIHILO CONCURRENTE SIMULTÁNEA
    with ThreadPoolExecutor(max_workers=len(archivos_por_procesar)) as executor:
        futuros = [
            executor.submit(ejecutar_invocacion_bedrock_hilo, doc_id, nombre_cliente, rfc_cliente, ano_fiscal, conceptos_sat)
            for doc_id in archivos_por_procesar
        ]
        for futuro in futuros:
            res = futuro.result()
            if res:
                resultados_redaccion_ia.append(res)

    print(f"🎯 Lote de redacción completado. Se despachan {len(resultados_redaccion_ia)} textos Markdown hacia el Paso 3.")
    event['archivos_redactados_ia'] = resultados_redaccion_ia
    return event
