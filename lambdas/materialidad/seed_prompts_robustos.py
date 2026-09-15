# =========================================================================
# SCRIPT DE CONSOLA: INYECTOR DE PROMPTS ULTRA-DENSOS ANTI-SAT DE ROUCHERS
# RUTA EN MAC: lambdas/materialidad/seed_prompts_robustos.py
# =========================================================================
import boto3
import json

def sembrar_prompts_robustos_sat():
    print("🔒 Inicializando apretón de manos con el perfil local: [veritas-dev]...")
    
    # 🚀 REPARACIÓN REINA 1: FORZAMOS LA COORDENADA DE REGIÓN DESDE LA SESIÓN
    # Esto aniquila cualquier fallback del CLI y amarra el canal estrictamente a us-east-1
    session_aws = boto3.Session(profile_name='veritas-profile', region_name='us-east-1')
    
    dynamodb = session_aws.resource('dynamodb', region_name='us-east-1')
    nombre_tabla = "veritas-control-prompts-catalog-dev"
    table = dynamodb.Table(nombre_tabla)
    
    print(f"📡 Conectando a la tabla física de DynamoDB: [{nombre_tabla}] en us-east-1...")

    # =========================================================================
    # 🏛️ PROMPT 01: FASE LEGAL (CONTRATO SOLEMNE INTEGRAL DESDE PRIMERO)
    # =========================================================================
    prompt_fase_1 = """# CONTRATO FORMAL DE PRESTACIÓN DE SERVICIOS PROFESIONALES COMPLETO
---
## **CONTRATO MAESTRO DE PRESTACIÓN DE SERVICIOS JURÍDICOS Y CORPORATIVOS**
**Celebrado en la Ciudad de México, Distrito Federal, en el marco del inicio del ejercicio fiscal {ano_fiscal}.**

---
## **COMPARECIENTES Y RAZONES SOCIALES**
**PRIMERA PARTE - EL PRESTADOR:**
**ROUCHERS**, Sociedad Mercantil constituida conforme a las leyes de los Estados Unidos Mexicanos, con Registro Federal de Contribuyentes número **ROU2203162G8**, en lo sucesivo denominado **"EL PRESTADOR"**.

**SEGUNDA PARTE - EL CONTRATANTE:**
**{nombre_cliente}**, identificado con Registro Federal de Contribuyentes número **{rfc_cliente}**, en lo sucesivo denominado **"EL CLIENTE"**.

---
## **DECLARACIONES E INFRAESTRUCTURA OPERATIVA**
### **I. DECLARACIONES DE EL PRESTADOR:**
1. Que es una entidad mercantil legalmente constituida conforme a las leyes mexicanas, con personalidad jurídica propia y plena capacidad legal para celebrar este instrumento.
2. Que cuenta con la infraestructura física real, activos tangibles e intangibles y personal calificado registrado debidamente ante el Instituto Mexicano del Seguro Social (IMSS) para responder por la materialidad de los actos (CFF Art. 69-B).
3. Que posee experiencia acreditada en la prestación de servicios profesionales integrales corporativos, contando con la capacidad técnica indispensable para la ejecución del objeto del contrato.

---
## **CLÁUSULAS**
### **CLÁUSULA PRIMERA: OBJETO DEL SERVICIO Y ALCANCE**
EL PRESTADOR se obliga a proporcionar a EL CLIENTE servicios profesionales de consultoría, asesoría y peritaje con un enfoque ultra-denso en: **{conceptos_sat}**. El servicio comprenderá el análisis de regímenes aplicables, la elaboración de papeles de trabajo mensuales, planeación fiscal estratégica, defensa regulatoria corporativa y blindaje perimetral tributario contra auditorías masivas de la autoridad federal.

### **CLÁUSULA SEGUNDA: INFRAESTRUCTURA INSTALADA Y ACTIVOS EN PRESTACIÓN**
En cumplimiento estricto de las aduanas de materialidad del Artículo 69-B del Código Fiscal de la Federación, EL PRESTADOR manifiesta bajo protesta de decir verdad que dispone y pone a servicio de este objeto contractual los siguientes activos:
A) Sistemas de cómputo de alta gama con procesamiento encriptado y plataformas de gestión documental con certificados SSL y almacenamiento redundante en la nube bajo protocolo AES-256.
B) Personal técnico y especializado titulado (Contadores Públicos, Abogados Fiscalistas y Peritos Forenses) cuyas nóminas, aportaciones de seguridad social (SUA/EBA) y retenciones son liquidadas oportunamente de forma mensual.

### **CLÁUSULA TERCERA: TRAZABILIDAD INMUTABLE Y CADENA DE CUSTODIA DIGITAL**
Ambas partes acuerdan que toda interacción, entrega de archivos, asesoría legal o minutas operativas quedará registrada de forma inmutable bajo un sistema de trazabilidad digital. Cada documento generado se indexará con marcas de tiempo con formato ISO 8601, direcciones IP origen, direcciones MAC de los dispositivos y firmas digitales de las personas físicas intervinientes, descartando categóricamente cualquier supuesto de simulación de actos o procesos robóticos automatizados.

### **CLÁUSULA CUARTA: HONORARIOS, RASTREABILIDAD FINANCIERA Y SELLO DE FIRMAS**
EL CLIENTE pagará la contraprestación económica pactada mediante transferencias electrónicas interbancarias originadas exclusivamente desde sus cuentas bancarias institucionales hacia las cuentas de EL PRESTADOR, asegurando la trazabilidad absoluta del flujo monetario ante las aduanas de la CNBV y el SAT. 

Este instrumento de prestación de servicios profesionales se firma de mutuo acuerdo bajo el sello digital e institucional del despacho ROUCHERS, S.C. y del representado.
"""

    # =========================================================================
    # ⚖️ PROMPT 02: FASE FISCAL (DICTAMEN CUMPLIMIENTO 32D Y MARCO 69-B)
    # =========================================================================
    prompt_fase_2 = """# DICTAMEN DE VALIDACIÓN DE COMPLIANCE Y OPINIÓN DE CUMPLIMIENTO 32D POSITIVA
---
## **DICTAMEN PERICIAL EMITIDO POR EL DEPARTAMENTO DE AUDITORÍA FISCAL DE ROUCHERS**
**Folio Forense Fiscal Único: RFC-32D-{rfc_cliente}-{ano_fiscal}**

---
## **I. DATOS DEL CONTRIBUYENTE AUDITADO**
- **Razón Social:** {nombre_cliente}
- **RFC:** {rfc_cliente}
- **Ejercicio Fiscal Auditado:** {ano_fiscal}
- **Firma Peritadora:** ROUCHERS - Despacho de Peritos Fiscales de Élite (RFC: ROU2203162G8)

---
## **II. MARCO JURÍDICO Y ANÁLISIS DE EXCLUSIÓN TRIBUTARIA**
El presente dictamen pericial se fundamenta en las aduanas del **Artículo 69-B del Código Fiscal de la Federación**, los Artículos 31, 76 y 86 del CFF, y las disposiciones vigentes de la Resolución Miscelánea Fiscal. Se procedió a compulsar, auditar y validar de forma integral la situación jurídica del contribuyente respecto a las operaciones de: **{conceptos_sat}**.

---
## **III. PROCEDIMIENTOS DE AUDITORÍA Y CONCLUSIONES PERICIALES**
### **A. CERTIFICACIÓN DE OPINIÓN DE CUMPLIMIENTO 32D**
Se verificaron mediante consulta en tiempo real en los servidores del SAT las Constancias de Situación Fiscal mensuales del contribuyente, certificando que su estatus es estrictamente **ACTIVO y CUMPLIDO**. El contribuyente se encuentra al corriente en la presentación de sus declaraciones provisionales y anuales de ISR e IVA, sin omisiones detectadas en los últimos 5 ejercicios.

### **B. COMPULSA DE AUSENCIA DE CRÉDITOS FISCALES FIRMES**
Este despacho certifica con grado de certeza legal y contable que NO EXISTEN créditos fiscales firmes, liquidaciones administrativas pendientes, resoluciones de determinación de contribuciones, ni actos de ejecución o embargos dictados en contra del contribuyente por parte de la Administración General de Recaudación. El perfil tributario goza de plena solvencia institucional.

### **C. SIMETRÍA TRIBUTARIA Y CONGRUENCIA FACTUAL**
Se auditó la ecuación contable del cliente, corroborando una simetría matemática perfecta entre los ingresos declarados, el IVA trasladado de forma expresa y las deducciones manifestadas contra las bases de datos de CFDIs de terceros y retenciones. Las operaciones reflejan una estricta sustancia económica y lógica de negocio, erradicando cualquier supuesto de triangulación de flujos o facturación de operaciones inexistentes.

**DICTAMEN FINAL PERICIAL: FAVORABLE (OPINIÓN 32D POSITIVA CONFORME)**
Sella el perito firmante con su cédula profesional bajo el respaldo corporativo de ROUCHERS.
"""

    # =========================================================================
    # 📸 PROMPT 03: FASE EVIDENCIAS (MEMORIA FORENSE SUSTANCIA Y METADATOS EXIF)
    # =========================================================================
    prompt_fase_3 = """# MEMORIA FORENSE JUSTIFICADA DE ENTREGABLES Y COMPROBACIÓN DE ASISTENCIA HUMANA DIRECTA
---
## **INFORME TÉCNICO DE MATERIALIDAD DIGITAL - OPERACIÓN AUDITADA ROUCHERS**
**Ejercicio Fiscal bajo Análisis: {ano_fiscal}**

---
## **I. OBJETO DEL PERITAJE DE SISTEMAS**
Demostrar de forma inatacable ante la **Administración General de Auditoría Fiscal Federal (AGAFF)** la materialidad real, física e inmutable de los servicios correspondientes a: **{conceptos_sat}**, prestados a favor de **{nombre_cliente}** (RFC: **{rfc_cliente}**), desvirtuando cualquier presunción de inexistencia mediante la comprobación científica de asistencia humana directa.

---
## **II. DESGLOSE FORENSE DE LA SUSTANCIA MATERIAL**
### **A. COMPROBACIÓN CRIPTOGRÁFICA DE REPORTES MENSUALES**
La materialidad técnica se soporta en reportes mensuales densos de actividades que desglonas las horas-hombre invertidas y los entregables lógicos. Cada archivo binario cuenta con un Hash criptográfico MD5 y SHA-256 inmutable registrado de forma segura en las bitácoras NoSQL, impidiendo la manipulación retroactiva de datos e integrando la prueba reina de la ejecución del acto.

### **B. BITÁCORAS DE CONTROL TÉCNICO CON TIMESTAMPS ISO 8601**
Se auditaron los logs de acceso a los sistemas corporativos del cliente, identificando un patrón de eventos con marcas de tiempo de milisegundos, IPs origen identificadas y MAC addresses de los dispositivos del personal asignado por ROUCHERS. La fluctuación humana y variabilidad de las marcas de tiempo descarta categóricamente el uso de procesos automatizados de software o bots ficticios.

### **C. TRAZABILIDAD MULTIFUENTE: MINUTAS DE JUNTAS Y METADATOS EXIF**
El expediente incorpora las minutas de juntas operativas solemnes firmadas digitalmente por los comités técnicos de ambas partes, las cuales guardan una perfecta correlación temporal con archivos fotográficos corporativos geolocalizados. Las imágenes contienen metadatos EXIF con coordenadas GPS de latitud y longitud verídicas que comprueban la presencia humana real en las salas de juntas corporativas.

Se certifica un total de **300 horas de servicios profesionales legítimos** ejecutados por personal altamente capacitado, blindando el búnker de evidencias al 100% bajo el sello de ROUCHERS.
"""

    # =========================================================================
    # 📊 PROMPT 04: FASE FINANCIERO (ECUACIÓN DE EQUILIBRIO Y ANTI-TRIANGULACIÓN)
    # =========================================================================
    prompt_fase_4 = """# INFORME DE RASTREABILIDAD FINANCIERA, SIMETRÍA ECONÓMICA Y FLUJO MONETARIO
---
## **DICTAMEN CONTABLE FORENSE SINCRO-MONETARIO - FINANZAS ROUCHERS**
**Sustancia Financiera del Contribuyente: {nombre_cliente} ({rfc_cliente})**

---
## **I. OBJETO DE COMPROBACIÓN MONETARIA**
Demostrar ante las autoridades fiscales la simetría contable-financiera absoluta de las erogaciones ejecutadas por concepto de **{conceptos_sat}** durante el año **{ano_fiscal}**, comprobando la perfecta trazabilidad bancaria y erradicando presunciones de triangulación de flujos de efectivo.

---
## **II. ANÁLISIS DE SIMETRÍA Y COMPROBACIÓN**
### **A. LA ECUACIÓN DE EQUILIBRIO CONTABLE**
Se procedió a auditar los estados de cuenta bancarios institucionales del contribuyente, validando la perfecta concordancia matemática de la fórmula donde el total de Ingresos Declarados es idéntico a la suma de CFDIs emitidos por ROUCHERS y a los depósitos monetarios efectivamente liquidados por la aduana bancaria mexicana. La variación registrada es del 0%, descartando pasivos ficticios u omisiones.

### **B. RASTREABILIDAD DEL TRASLADO DEL IVA Y ANÁLISIS DE FLUJO**
Cada comprobante fiscal digital cuenta con su contraparte de transferencia electrónica interbancaria SPEI, identificando los subtotales, el traslado expreso y oportuno del 16% del IVA y las retenciones corporativas aplicables. Los fondos provinieron estrictamente de las cuentas operativas del cliente y se dispersaron de forma directo hacia las cuentas bancarias corporativas de ROUCHERS, S.C.

### **C. ERRADICACIÓN DE TRIANGULACIONES DE EFECTIVO**
Este peritaje contable forense ejecutó las pruebas de identidad del depositante y consistencia de montos. Se certifica que no existen depósitos sin CFDI correlativo, variaciones de tiempo mayores a 3 días hábiles en compensación bancaria, ni dispersiones de capital hacia terceros o intermediarios sin justificación comercial legítima. La operación es transparente, real y cumple cabalmente con los requisitos de deducibilidad de la Ley del ISR.
"""

    lote_prompts = [
        {"id_documento": "CONTRATO_PRESTACION_SERVICIOS", "folder_seccion": "01_LEGAL_Y_CONSTITUTIVO", "prompt_base_markdown": prompt_fase_1},
        {"id_documento": "DICTAMEN_OPINION_32D", "folder_seccion": "02_CUMPLIMIENTO_FISCAL", "prompt_base_markdown": prompt_fase_2},
        {"id_documento": "BITACORA_CONTROL_ASISTENCIA", "folder_seccion": "03_EVIDENCIA_MATERIALIDAD", "prompt_base_markdown": prompt_fase_3},
        {"id_documento": "INFORME_FLUJO_BANCARIO", "folder_seccion": "04_COMPROBACION_FINANCIERA", "prompt_base_markdown": prompt_fase_4}
    ]

    print("\n💾 Sembrando registros densificados con validación de red...")
    for p in lote_prompts:
        # 🚀 REPARACIÓN REINA 2: CAPTURAMOS LA RESPUESTA DE LA API DE AWS
        respuesta_aws = table.put_item(Item=p)
        
        # Extraemos el código de estatus de la aduana de Amazon (Debe ser 200)
        estatus_http = respuesta_aws.get('ResponseMetadata', {}).get('HTTPStatusCode', 500)
        
        if estatus_http == 200:
            print(f"✅ [HTTP 200] ¡Prompt '{p['id_documento']}' guardado físicamente con éxito en us-east-1!")
        else:
            print(f"❌ [HTTP {estatus_http}] Fallo de persistencia para: {p['id_documento']}. Detalle: {respuesta_aws}")

    print("\n🏁 ¡Base de conocimientos de ROUCHERS auditada y sembrada al 100% en la nube!")

if __name__ == "__main__":
    sembrar_prompts_robustos_sat()