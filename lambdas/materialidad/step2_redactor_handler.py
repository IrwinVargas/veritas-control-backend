# =========================================================================
# REESTRUCTURACIÓN CORE PASO 2: ESTRATEGIA DOCUMENTAL POR SECCIÓN SAT
# RUTA EN MAC: lambdas/materialidad/step2_redactor_handler.py
# =========================================================================
import os
import json
import boto3

bedrock_client = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

# =========================================================================
# 🏗️ REGINA DE PATRÓN STRATEGY: CADA DOCUMENTO DE LAS 4 SECCIONES TIENE SU PROMPT
# Claude 4.5 redacta desde el título solemne hasta el fin barriendo textos en duro
# =========================================================================
class BaseDocumentStrategy:
    def construir_prompt_pericial(self, nombre, rfc, ano, conceptos):
        raise NotImplementedError

# --- FASE 01: ESTRATEGIAS LEGALES ---
class ContratoSolemneStrategy(BaseDocumentStrategy):
    def construir_prompt_pericial(self, nombre, rfc, ano, conceptos):
        return f"""Actúa como un Abogado Defensor Corporativo de la firma ROUCHERS (RFC: ROU2203162G8).
        Redacta de forma íntegra un CONTRATO FORMAL DE PRESTACIÓN DE SERVICIOS PROFESIONALES.
        - Representado: {nombre} (RFC: {rfc}) | Ejercicio Fiscal: {ano}
        - Clausulado Core: Inicia desde el Título solemne, Declaraciones, Cláusula PRIMERA (Objeto exacto del servicio: {conceptos}), SEGUNDA (Infraestructura instalada y activos), TERCERA (Trazabilidad), CUARTA (Vigencia) hasta el cierre e inyección de cuadros de firmas de ambas partes."""

# --- FASE 02: ESTRATEGIAS FISCALES / CUMPLIMIENTO ---
class DictamenOpinion32DStrategy(BaseDocumentStrategy):
    def construir_prompt_pericial(self, nombre, rfc, ano, conceptos):
        return f"""Actúa como un Perito Fiscal de Élite de ROUCHERS.
        Redacta un DICTAMEN DE VALIDACIÓN DE COMPLIANCE Y OPINIÓN DE CUMPLIMIENTO 32D POSITIVA.
        - Contribuyente Auditado: {nombre} (RFC: {rfc}) | Ejercicio Fiscal: {ano}
        - Marco Jurídico: Fundaméntalo en las aduanas del Artículo 69-B del CFF. Certifica la veracidad de las constancias de situación fiscal del mes, la ausencia de créditos fiscales firmes y la simetría tributaria de {conceptos}."""

# --- FASE 03: ESTRATEGIAS DE EVIDENCIAS / SUSTANCIA MATERIAL ---
class BitacoraMaterialidadStrategy(BaseDocumentStrategy):
    def construir_prompt_pericial(self, nombre, rfc, ano, conceptos):
        return f"""Actúa como un Auditor Forense de Sistemas de ROUCHERS.
        Redacta una MEMORIA FORENSE JUSTIFICADA DE ENTREGABLES Y COMPROBACIÓN DE ASISTENCIA HUMANA DIRECTA.
        - Cliente: {nombre} (RFC: {rfc}) | Ejercicio Fiscal: {ano}
        - Evidencias: Cita y argumenta la existencia inmutable de reportes mensuales de actividades, bitácoras de control técnico, minutas de juntas operativas con timestamps y archivos fotográficos geolocalizados que demuestran mecánicamente la materialidad de {conceptos}."""

# --- FASE 04: ESTRATEGIAS FINANCIERAS / COMPROBACIÓN ---
class AnalisisFlujoBancarioStrategy(BaseDocumentStrategy):
    def construir_prompt_pericial(self, nombre, rfc, ano, conceptos):
        return f"""Actúa como un Perito Contable Forense de la firma ROUCHERS.
        Redacta un INFORME DE RASTREABILIDAD FINANCIERA, SIMETRÍA ECONÓMICA Y FLUJO MONETARIO.
        - Cliente: {nombre} (RFC: {rfc}) | Ejercicio Fiscal: {ano}
        - Finanzas: Desglosa la correlación inalterable entre los CFDIs emitidos por los conceptos de [{conceptos}], el traslado expreso del IVA y las salidas monetarias registradas en los estados de cuenta bancarios institucionales, erradicando presunciones de triangulación de efectivo."""

# =========================================================================
# 🏭 EL FACTORY DE ARCHIVOS DE LA SUITE VERITAS
# Registra cada archivo obligatorio mapeado exactamente a su respectiva sección SAT
# =========================================================================
DOCUMENT_FACTORY = {
    "CONTRATO_PRESTACION_SERVICIOS": {"strategy": ContratoSolemneStrategy(), "folder": "01_LEGAL_Y_CONSTITUTIVO"},
    "DICTAMEN_OPINION_32D": {"strategy": DictamenOpinion32DStrategy(), "folder": "02_CUMPLIMIENTO_FISCAL"},
    "BITACORA_CONTROL_ASISTENCIA": {"strategy": BitacoraMaterialidadStrategy(), "folder": "03_EVIDENCIA_MATERIALIDAD"},
    "INFORME_FLUJO_BANCARIO": {"strategy": AnalisisFlujoBancarioStrategy(), "folder": "04_COMPROBACION_FINANCIERA"}
}

def handler(event, context):
    print("🤖 Paso 2 Activo: Evaluando Petición mediante Fábrica de Secciones...")
    
    # Captura de tokens dinámicos enviados por tu Front-End en React
    tipo_peticion = event.get('tipo_peticion', 'GENERAR_TODAS')  # GENERAR_TODAS | UNICA_SECCION | UNICO_ARCHIVO
    seccion_target = event.get('seccion_target', '')            # 01_LEGAL_Y_CONSTITUTIVO, 02_CUMPLIMIENTO_FISCAL, etc.
    archivo_target = event.get('archivo_target', '')            # CONTRATO_PRESTACION_SERVICIOS, etc.
    
    nombre_cliente = event.get('nombre_cliente', 'Contribuyente Auditado')
    rfc_cliente = event.get('rfc_cliente', '')
    ano_fiscal = event.get('ano_fiscal', '2026')
    conceptos_sat = event.get('string_catalogo_ia', 'Servicios profesionales integrales corporativos')

    # 🚀 DETERMINACIÓN ELÁSTICA DEL LOTE DE ARCHIVOS (MÁXIMA RESILIENCIA)
    archivos_por_procesar = []
    
    if tipo_peticion == 'GENERAR_TODAS':
        archivos_por_procesar = list(DOCUMENT_FACTORY.keys())
    elif tipo_peticion == 'UNICA_SECCION':
        archivos_por_procesar = [k for k, v in DOCUMENT_FACTORY.items() if v["folder"] == seccion_target]
    elif tipo_peticion == 'UNICO_ARCHIVO':
        archivos_por_procesar = [archivo_target] if archivo_target in DOCUMENT_FACTORY else ["CONTRATO_PRESTACION_SERVICIOS"]

    resultados_redaccion_ia = []

    # Gatillamos la iteración mandando ráfagas a Claude 4.5 Haiku
    for doc_id in archivos_por_procesar:
        if doc_id not in DOCUMENT_FACTORY:
            continue
            
        config = DOCUMENT_FACTORY[doc_id]
        strategy = config["strategy"]
        folder_sat = config["folder"]

        # Construcción del prompt extendido pericial
        prompt_final = strategy.construir_prompt_pericial(nombre_cliente, rfc_cliente, ano_fiscal, conceptos_sat)

        body_request = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt_final}]
        })

        try:
            model_id_real = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
            print(f"📡 Invocando a Claude 4.5 para armar el documento: [{doc_id}] de la sección [{folder_sat}]")
            
            response = bedrock_client.invoke_model(
                modelId=model_id_real, contentType="application/json", accept="application/json", body=body_request
            )
            response_body = json.loads(response.get('body').read())
            texto_ia_generado = response_body['content']['text'].replace("```html", "").replace("```", "").strip()
            
            resultados_redaccion_ia.append({
                "id_documento": doc_id,
                "nombre_archivo": f"{doc_id}_{ano_fiscal}.pdf",
                "folder_seccion": folder_sat,
                "prosa_completa_ia": texto_ia_generado
            })
        except Exception as e:
            print(f"❌ Error crítico en la hebra del documento {doc_id}: {str(e)}")

    # Propagamos los entregables empaquetados hacia el Paso 3 (Escultor ReportLab)
    event['archivos_redactados_ia'] = resultados_redaccion_ia
    return event
