# =========================================================================
# SCRIPT SEMILLA COMPLETO: POBLADOR COMPUESTO DE LOS 9 PROMPTS DEL SAT
# RUTA EN MAC: lambdas/materialidad/seed_prompts_robustos.py
# =========================================================================
import boto3
import json
import sys

def sembrar_catalogo_completo_rouchers():
    print("🔒 Inicializando sesión segura con el perfil local: [veritas-dev]...")
    sys.stdout.flush()
    
    session_aws = boto3.Session(profile_name='veritas-profile', region_name='us-east-1')
    dynamodb = session_aws.resource('dynamodb', region_name='us-east-1')
    nombre_tabla = "veritas-control-prompts-catalog-dev"
    table = dynamodb.Table(nombre_tabla)
    
    print(f"📡 Conectando en bloque batch a: [{nombre_tabla}] en us-east-1...")
    sys.stdout.flush()

    # --- FASE 01 PROMPTS LEGALES ---
    p_contrato = "Escribe el CONTRATO MAESTRO DE PRESTACIÓN DE SERVICIOS PROFESIONALES completo para {nombre_cliente} ({rfc_cliente}) ejercicio {ano_fiscal}. Objeto: {conceptos_sat}. Detalla obligaciones, infraestructura del prestador ROUCHERS (RFC: ROU2203162G8), vigencia anual y firmas formales."
    p_acta = "Escribe el ACTA DE ASAMBLEA EXTRAORDINARIA DE RESPALDO CORPORATIVO de ROUCHERS S.C. para la cuenta de {nombre_cliente} ({rfc_cliente}) año {ano_fiscal}, certificando la asignación de activos fijos, servidores AWS dedicados y la ausencia de subcontrataciones."
    p_id_legal = "Escribe la CÉDULA PERICIAL DE PERSONALIDAD JURÍDICA Y ACREDITACIÓN del representante legal y profesionistas de ROUCHERS asignados a la cuenta de {nombre_cliente} ({rfc_cliente}), citando las cédulas profesionales de la SEP para avalar la idoneidad técnica de {conceptos_sat}."

    # --- FASE 02 PROMPTS FISCALES ---
    p_32d = "Escribe el DICTAMEN DE VALIDACIÓN DE COMPLIANCE Y OPINIÓN 32D POSITIVA de ROUCHERS para {nombre_cliente} ({rfc_cliente}) ejercicio {ano_fiscal}. Fundaméntalo en el Art. 69-B del CFF certificando la constancia mensual ACTIVA y la ausencia total de créditos fiscales."
    p_constancia = "Escribe la CÉDULA DE IDENTIFICACIÓN DE DOMICILIO Y ALTA DE SUCURSALES de ROUCHERS y de {nombre_cliente} ({rfc_cliente}), certificando la correspondencia del domicilio fiscal registrado, la capacidad instalada física real y la simetría contable de {conceptos_sat}."

    # --- FASE 03 PROMPTS EVIDENCIAS ---
    p_bitacora = "Escribe la BITÁCORA CRIPTOGRÁFICA DE LOGS TÉCNICOS CON TIMESTAMPS para {nombre_cliente} ({rfc_cliente}) año {ano_fiscal}. Detalla registros con formato ISO 8601, direcciones IP origen,MAC addresses y ID de sesiones de ROUCHERS que demuestren asistencia humana directa y descarten automatización."
    p_multimedia = "Escribe el INFORME DE MEMORIA FOTOGRÁFICA CORPORATIVA GEOLOCALIZADA EXIF para {nombre_cliente} ({rfc_cliente}) ejercicio {ano_fiscal}. Cita metadatos EXIF con coordenadas GPS reales de latitud y longitud que comprueben físicamente las juntas presenciales sobre {conceptos_sat}."

    # --- FASE 04 PROMPTS FINANCIEROS ---
    p_flujo = "Escribe el INFORME DE SIMETRÍA ECONÓMICA Y ECUACIÓN DE EQUILIBRIO CONTABLE de ROUCHERS para {nombre_cliente} ({rfc_cliente}) año {ano_fiscal}. Valida que los CFDIs de {conceptos_sat} guardan correspondencia exacta con los estados de cuenta bancarios y depósitos SPEI."
    p_xml = "Escribe la CÉDULA DE INTEGRIDAD DE EROGAPIONES E IMPUESTOS TRASLADADOS para {nombre_cliente} ({rfc_cliente}) año {ano_fiscal}. Realiza la conciliación masiva de XMLs CFDI emitidos, certificando el traslado oportuno del 16% de IVA y erradicando triangulación de fondos."

    lote_completo_9_docs = [
        {"id_documento": "CONTRATO_PRESTACION_SERVICIOS", "folder_seccion": "01_LEGAL_Y_CONSTITUTIVO", "prompt_base_markdown": p_contrato},
        {"id_documento": "ACTA_CONSTITUTIVA_RESPALDO", "folder_seccion": "01_LEGAL_Y_CONSTITUTIVO", "prompt_base_markdown": p_acta},
        {"id_documento": "IDENTIFICACION_REPRESENTANTE_LEGAL", "folder_seccion": "01_LEGAL_Y_CONSTITUTIVO", "prompt_base_markdown": p_id_legal},
        
        {"id_documento": "DICTAMEN_OPINION_32D", "folder_seccion": "02_CUMPLIMIENTO_FISCAL", "prompt_base_markdown": p_32d},
        {"id_documento": "CONSTANCIA_SITUACION_FISCAL_CEDULA", "folder_seccion": "02_CUMPLIMIENTO_FISCAL", "prompt_base_markdown": p_constancia},
        
        {"id_documento": "BITACORA_CONTROL_ASISTENCIA", "folder_seccion": "03_EVIDENCIA_MATERIALIDAD", "prompt_base_markdown": p_bitacora},
        {"id_documento": "MEMORIA_FOTOGRAFICA_GEOLOCALIZADA", "folder_seccion": "03_EVIDENCIA_MATERIALIDAD", "prompt_base_markdown": p_multimedia},
        
        {"id_documento": "INFORME_FLUJO_BANCARIO", "folder_seccion": "04_COMPROBACION_FINANCIERA", "prompt_base_markdown": p_flujo},
        {"id_documento": "CONCILIACION_XML_COMPROBANTES", "folder_seccion": "04_COMPROBACION_FINANCIERA", "prompt_base_markdown": p_xml}
    ]

    print("🚀 Transmitiendo el compendio de los 9 documentos core del SAT por lote...")
    sys.stdout.flush()
    
    with table.batch_writer() as batch:
        for item in lote_completo_9_docs:
            batch.put_item(Item=item)
            print(f"   📦 Indexado con éxito: [{item['id_documento']}] en la carpeta [{item['folder_seccion']}]")
            sys.stdout.flush()
            
    print("\n🏁 [HTTP 200] ¡Base de conocimientos NoSQL nutrida al 100% con los 9 instrumentos obligatorios!")
    sys.stdout.flush()

if __name__ == "__main__":
    sembrar_catalogo_completo_rouchers()
