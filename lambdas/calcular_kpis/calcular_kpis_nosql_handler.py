# backend/lambdas/finanzas_dashboard/calcular_kpis_nosql_handler.py
import os
import json
import boto3
import pandas as pd
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def float_to_decimal(val):
    try:
        if pd.isna(val) or val is None:
            return Decimal('0.00')
        return Decimal(str(round(float(val), 2)))
    except:
        return Decimal('0.00')

def handler(event, context):
    try:
        print("📊 Microservicio NoSQL v5 activado. Analizando estructura real del SAT...")
        
        payload_parser = event if isinstance(event, dict) else json.loads(event)
        tenant_id = payload_parser.get('tenant_id')
        facturas = payload_parser.get('facturas', [])

        if not facturas:
            print("⚠️ El arreglo de facturas viene vacio.")
            return {'success': True}

        # Cargamos la matriz de Pandas directo desde el JSON en la RAM
        df = pd.DataFrame(facturas)

        # 🚀 PASO 1: Limpieza uniforme de cabeceras en minúsculas
        df.columns = df.columns.str.strip().str.lower()

        # 🔍 1. DETECTOR JERÁRQUICO ESTRICTO DE LA COLUMNA DE TIPO/EFECTO
        col_tipo = next((c for c in df.columns if any(p in c for p in ['comprobante', 'efecto', 'tipo'])), df.columns)
        
        # 🔍 2. DETECTOR JERÁRQUICO ESTRICTO DE LA COLUMNA DE DINERO (TOTAL Y SUBTOTAL)
        col_total = next((c for c in df.columns if 'total' in c and 'impuesto' not in c and 'iva' not in c), None)
        if not col_total:
            col_total = next((c for c in df.columns if 'monto' in c or 'importe' in c), df.columns[-1])
            
        col_subtotal = next((c for c in df.columns if 'sub' in c and c != col_total), col_total)
        col_fecha = next((c for c in df.columns if 'fecha' in c or 'timbrado' in c), df.columns)

        print(f"🎯 Red de Mapeo Realizada -> Tipo: [{col_tipo}], Total: [{col_total}], Subtotal: [{col_subtotal}]")

        # 🚀 PASO 2: LIMPIEZA POLIMÓRFICA DE MONEDA MEXICANA ($307.252,08)
        # Remueve el signo $, quita los puntos de los miles y convierte la coma decimal en punto para que Python lo entienda
        for col_money in [col_total, col_subtotal]:
            if col_money in df.columns:
                df[col_money] = df[col_money].astype(str).str.replace('$', '', regex=False)
                df[col_money] = df[col_money].str.replace('.', '', regex=False)
                df[col_money] = df[col_money].str.replace(',', '.', regex=False)
                df[col_money] = pd.to_numeric(df[col_money], errors='coerce').fillna(0.0)

        # Homologamos el tipo de comprobante celda por celda de forma segura
        df[col_tipo] = df[col_tipo].apply(lambda x: str(x).upper().strip() if pd.notna(x) else 'DESCONOCIDO')

        # 🔒 SEGMENTACIÓN MULTI-TENANT EXACTA DEL SAT
        df_ingresos = df[df[col_tipo].apply(lambda x: str(x).startswith(('I', '1', 'ING')))]
        df_egresos = df[df[col_tipo].apply(lambda x: str(x).startswith(('E', '2', 'EGR')))]

        print(f"📈 Sumas calibradas -> {len(df_ingresos)} Ingresos y {len(df_egresos)} Egresos localizados en la RAM.")

        # Computación analítica de las 8 métricas requeridas por el negocio
        ventas_totales = float(df_ingresos[col_total].sum())
        ingresos_totales = float(df_ingresos[col_subtotal].sum()) # Base imponible sin IVA
        egresos_totales = float(df_egresos[col_total].sum())
        
        flujo_caja = ventas_totales - egresos_totales
        ticket_promedio = ventas_totales / len(df_ingresos) if len(df_ingresos) > 0 else 0.0
        comisiones_totales = ventas_totales * 0.035
        
        margen_ganancia = ((ventas_totales - egresos_totales) / ventas_totales * 100) if ventas_totales > 0 else 0.0
        roi = (flujo_caja / egresos_totales * 100) if egresos_totales > 0 else 0.0

        # Agrupación temporal para el balance de la gráfica espejo de React
        df['fecha_parsed'] = pd.to_datetime(df[col_fecha], errors='coerce')
        df['mes_grafica'] = df['fecha_parsed'].dt.strftime('%b %Y').fillna('Sin Fecha')

        df_mes_ingresos = df[df[col_tipo].apply(lambda x: str(x).startswith(('I', '1', 'ING')))]
        df_mes_egresos = df[df[col_tipo].apply(lambda x: str(x).startswith(('E', '2', 'EGR')))]

        ingresos_mensuales = df_mes_ingresos.groupby('mes_grafica')[col_total].sum()
        egresos_mensuales = df_mes_egresos.groupby('mes_grafica')[col_total].sum()

        meses_unicos = sorted(list(set(df['mes_grafica'].dropna())))
        data_grafica = []
        for mes in meses_unicos:
            if mes == 'Sin Fecha': continue
            data_grafica.append({
                "name": str(mes),
                "ingresos": float_to_decimal(ingresos_mensuales.get(mes, 0.0)),
                "egresos": float_to_decimal(egresos_mensuales.get(mes, 0.0))
            })

        # 🔌 Escritura NoSQL directa hacia Amazon DynamoDB
        nombre_tabla = os.environ.get('DYNAMODB_TABLE')
        table = dynamodb.Table(nombre_tabla)

        payload_nosql = {
            'tenant_id': tenant_id,
            'ventas_totales': float_to_decimal(ventas_totales),
            'ingresos_totales': float_to_decimal(ingresos_totales),
            'egresos_totales': float_to_decimal(egresos_totales),
            'flujo_caja': float_to_decimal(flujo_caja),
            'ticket_promedio': float_to_decimal(ticket_promedio),
            'comisiones_totales': float_to_decimal(comisiones_totales),
            'margen_ganancia': float_to_decimal(margen_ganancia),
            'roi': float_to_decimal(roi),
            'grafica_historica': data_grafica
        }

        table.put_item(Item=payload_nosql)
        print(f"🎯 Éxito rotundo: Indexado el balance del SAT de {format(ventas_totales, '.2f')} MXN para el bufete {tenant_id}.")
        
        return {'success': True}
        
    except Exception as e:
        print(f"❌ Error crítico en el calculador NoSQL: {str(e)}")
        raise e
