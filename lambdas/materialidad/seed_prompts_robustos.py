# =========================================================================
# SCRIPT DE CONSOLA: INYECTOR COMPUESTO DE PROMPTS REALES ANTI-SAT (DENSOS)
# RUTA EN MAC: lambdas/materialidad/seed_prompts_robustos.py
# =========================================================================
import boto3
import json

def sembrar_prompts_reales_sat():
    print("🔒 Inicializando sesión segura con el perfil local: [veritas-dev]...")
    session_aws = boto3.Session(profile_name='veritas-profile', region_name='us-east-1')
    dynamodb = session_aws.resource('dynamodb', region_name='us-east-1')
    
    nombre_tabla = "veritas-control-prompts-catalog-dev"
    table = dynamodb.Table(nombre_tabla)

    # 🚀 PROMPT DE FASE 1: CONTRATO SOLEMNE CON ESPECIFICACIÓN REAL ANTI-MACHOTE
    prompt_fase_1 = """# CONTRATO FORMAL DE PRESTACIÓN DE SERVICIOS PROFESIONALES COMPLETO
---
## **CONTRATO MAESTRO DE PRESTACIÓN DE SERVICIOS PROFESIONALES CORPORATIVOS**
**Celebrado entre ROUCHERS (EL PRESTADOR) y {nombre_cliente} (EL CLIENTE) para el ejercicio {ano_fiscal}.**

---
## **DECLARACIONES E INFRAESTRUCTURA REAL (CFF ART. 69-B)**
I. EL PRESTADOR declara que es una Sociedad constituida conforme a las leyes mexicanas (RFC: ROU2203162G8), con personal real, titulado y asegurado ante el IMSS, respaldado por activos tecnológicos y oficinas físicas aptas para ejecutar el objeto de este instrumento.
II. EL CLIENTE declara bajo protesta de decir verdad que requiere la asesoría especializada para sus operaciones de: **{conceptos_sat}**.

---
## **CLÁUSULAS ESPECÍFICAS DE ALCANCE Y FONDO (MÍNIMO 8 PÁRRAFOS DENSOS)**
### **CLÁUSULA PRIMERA: OBJETO DETALLADO Y ENTREGABLES MEDIBLES**
EL PRESTADOR se obliga a ejecutar de forma específica la prestación de: **{conceptos_sat}**. Esto comprende estrictamente: la elaboración mensual de declaraciones, la auditoría forense de sistemas con logs validados, conciliaciones bancarias indexadas y la entrega de reportes ejecutivos mensuales firmados por el perito responsable, evitando promesas vagas o generalizadas.

### **CLÁUSULA SEGUNDA: TRAZABILIDAD HUMANA DIRECTA Y METADATOS EXIF**
Ambas partes acuerdan que la materialidad del servicio se comprobará de forma inmutable mediante una cadena de custodia digital en S3, integrando bitácoras de control técnico con timestamps ISO 8601 (Ips origen, MAC addresses) y archivos fotográficos de juntas con metadatos de geolocalización satelital (GPS Latitud y Longitud) reales de las oficinas de {nombre_cliente}.

### **CLÁUSULA TERCERA: HONORARIOS CALENDARIO, RESCISIÓN Y JURISDICCIÓN COMERCIAL**
El costo total de los servicios profesionales será cubierto estrictamente a través de transferencias electrónicas interbancarias originadas desde las cuentas corporativas institucionales del cliente. Se estipula una vigencia forzosa del 1 de enero al 31 de diciembre de {ano_fiscal}, una cláusula penal por mora del 1.5% mensual, y causas de rescisión explícitas por incumplimiento de entrega documental, bajo la jurisdicción de los tribunales de la Ciudad de México.
"""

    lote_prompts = [
        {"id_documento": "CONTRATO_PRESTACION_SERVICIOS", "folder_seccion": "01_LEGAL_Y_CONSTITUTIVO", "prompt_base_markdown": prompt_fase_1}
    ]

    print("🚀 Transmitiendo lote de prompts densificados hacia DynamoDB...")
    with table.batch_writer() as batch:
        for item in lote_prompts:
            batch.put_item(Item=item)
            print(f"   📦 Encapsulado en lote: [{item['id_documento']}]")
            
    print("\n🏁 [HTTP 200] ¡Base de conocimientos de ROUCHERS robustecida con éxito en us-east-1!")

if __name__ == "__main__":
    sembrar_prompts_reales_sat()
