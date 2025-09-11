"""
Script para calcular X10_IE - Infraestructura Educativa (Preliminar)
Metodología: Índice de Infraestructura Digital y Tecnológica

Fórmula: X10_IE = (Conectividad_Digital × 0.5) + (Equipamiento_Tecnológico × 0.3) + (Infraestructura_Eléctrica × 0.2)

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import os

def calcular_x10_ie_preliminar():
    """
    Calcula X10_IE usando datos de conectividad y equipamiento disponibles
    """
    
    print("=== CALCULANDO X10_IE INFRAESTRUCTURA EDUCATIVA PRELIMINAR ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Obtener instituciones target
    df_target = pd.read_sql_query("""
        SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION, NUMERO_FYA, X2_TR
        FROM indices_metodologicos
    """, conn)
    
    print(f"1. INSTITUCIONES TARGET: {len(df_target)}")
    
    # 2. Procesar datos de conectividad y equipamiento
    print(f"\n2. PROCESANDO DATOS CONECTIVIDAD_EQUIPAMIENTO:")
    
    df_conectividad_raw = pd.read_sql_query("""
        SELECT 
            codigo_modular,
            la_iiee_cuenta_actualmente_con_servicio_operativo_de_internet,
            mbps_max,
            ambientes_que_cuentan_con_internet_extendida_cableado_o_red_wifi,
            pc_de_escritorio_numero_de_equipos_que_tiene_la_ie,
            laptop_numero_de_equipos_que_tiene_la_ie,
            tablet_numero_de_equipos_que_tiene_la_ie,
            proyectores_numero_de_equipos_que_tiene_la_ie,
            pc_de_escritorio_numero_de_equipos_en_optimas_condiciones_que_ti,
            laptop_numero_de_equipos_en_optimas_condiciones_que_tiene_la_ie,
            tablet_numero_de_equipos_en_optimas_condiciones_que_tiene_la_ie,
            proyectores,
            la_ie_cuenta_con_suministro_de_electricidad_de_algun_tipo,
            tipo_de_fluido_electrico
        FROM conectividad_equipamiento
        WHERE codigo_modular IS NOT NULL
    """, conn)
    
    print(f"   Registros conectividad: {len(df_conectividad_raw)}")
    print(f"   Instituciones únicas: {df_conectividad_raw['codigo_modular'].nunique()}")
    
    # 3. Procesar por institución (agregando registros duplicados)
    print(f"\n3. AGREGANDO DATOS POR INSTITUCIÓN:")
    
    calculo_x10_ie = []
    
    for codigo in df_conectividad_raw['codigo_modular'].unique():
        df_inst = df_conectividad_raw[df_conectividad_raw['codigo_modular'] == codigo]
        
        # COMPONENTE 1: Conectividad Digital (peso 0.5)
        internet_operativo = 1.0 if (df_inst['la_iiee_cuenta_actualmente_con_servicio_operativo_de_internet'] == 'Si').any() else 0.0
        
        # Mbps promedio (normalizar hasta 100 Mbps máximo) - limpieza de datos
        mbps_valores = df_inst['mbps_max'].dropna()
        mbps_promedio = 0
        for val in mbps_valores:
            try:
                # Intentar convertir a número
                val_numeric = float(str(val).replace('NO', '0').split(' - ')[0])
                mbps_promedio = max(mbps_promedio, val_numeric)
            except:
                # Si falla conversión, usar 0
                continue
        mbps_normalizado = min(1.0, mbps_promedio / 100.0) if mbps_promedio > 0 else 0.0
        
        # Ambientes con internet (binario)
        ambientes_internet = 1.0 if df_inst['ambientes_que_cuentan_con_internet_extendida_cableado_o_red_wifi'].notna().any() else 0.0
        
        conectividad_digital = (internet_operativo * 0.6) + (mbps_normalizado * 0.2) + (ambientes_internet * 0.2)
        
        # COMPONENTE 2: Equipamiento Tecnológico (peso 0.3)
        # Función para limpiar y convertir valores numéricos
        def convertir_a_numero(serie):
            total = 0
            for val in serie.fillna(0):
                try:
                    if pd.isna(val) or val == '' or str(val).lower() in ['nan', 'none', 'null']:
                        continue
                    total += float(str(val).replace(',', '').split()[0])  # Tomar primer número
                except:
                    continue
            return total
        
        # Equipos totales
        pc_total = convertir_a_numero(df_inst['pc_de_escritorio_numero_de_equipos_que_tiene_la_ie'])
        laptop_total = convertir_a_numero(df_inst['laptop_numero_de_equipos_que_tiene_la_ie'])
        tablet_total = convertir_a_numero(df_inst['tablet_numero_de_equipos_que_tiene_la_ie'])
        proyector_total = convertir_a_numero(df_inst['proyectores_numero_de_equipos_que_tiene_la_ie'])
        
        equipos_total = pc_total + laptop_total + tablet_total + proyector_total
        
        # Equipos funcionales
        pc_funcional = convertir_a_numero(df_inst['pc_de_escritorio_numero_de_equipos_en_optimas_condiciones_que_ti'])
        laptop_funcional = convertir_a_numero(df_inst['laptop_numero_de_equipos_en_optimas_condiciones_que_tiene_la_ie'])
        tablet_funcional = convertir_a_numero(df_inst['tablet_numero_de_equipos_en_optimas_condiciones_que_tiene_la_ie'])
        proyector_funcional = convertir_a_numero(df_inst['proyectores'])
        
        equipos_funcionales = pc_funcional + laptop_funcional + tablet_funcional + proyector_funcional
        
        # Ratio funcionalidad (máximo 1.0)
        if equipos_total > 0:
            ratio_funcionalidad = min(1.0, equipos_funcionales / equipos_total)
            # Bonus por cantidad (hasta 20 equipos = 1.0)
            bonus_cantidad = min(1.0, equipos_total / 20.0)
            equipamiento_tecnologico = (ratio_funcionalidad * 0.7) + (bonus_cantidad * 0.3)
        else:
            equipamiento_tecnologico = 0.0
        
        # COMPONENTE 3: Infraestructura Eléctrica (peso 0.2)
        electricidad = 1.0 if (df_inst['la_ie_cuenta_con_suministro_de_electricidad_de_algun_tipo'] == 'Si').any() else 0.0
        
        # Tipo de fluido eléctrico (calidad)
        tipos_electrico = df_inst['tipo_de_fluido_electrico'].dropna()
        if len(tipos_electrico) > 0:
            tipo_principal = tipos_electrico.iloc[0]
            if 'red pública' in str(tipo_principal).lower():
                calidad_electrica = 1.0
            elif 'generador' in str(tipo_principal).lower():
                calidad_electrica = 0.7
            elif 'solar' in str(tipo_principal).lower():
                calidad_electrica = 0.8
            else:
                calidad_electrica = 0.5  # Otros
        else:
            calidad_electrica = 0.5 if electricidad > 0 else 0.0
        
        infraestructura_electrica = (electricidad * 0.7) + (calidad_electrica * 0.3)
        
        # CÁLCULO FINAL X10_IE
        x10_ie = (conectividad_digital * 0.5) + (equipamiento_tecnologico * 0.3) + (infraestructura_electrica * 0.2)
        
        calculo_x10_ie.append({
            'codigo_modular': str(codigo),
            'X10_IE': round(x10_ie, 4),
            'conectividad_digital': round(conectividad_digital, 4),
            'equipamiento_tecnologico': round(equipamiento_tecnologico, 4),
            'infraestructura_electrica': round(infraestructura_electrica, 4),
            'internet_operativo': internet_operativo,
            'mbps_promedio': round(mbps_promedio, 1),
            'equipos_total': int(equipos_total),
            'equipos_funcionales': int(equipos_funcionales),
            'tiene_electricidad': electricidad,
            'fuente': 'conectividad_equipamiento',
            'metodo': 'calculo_directo'
        })
    
    df_calculados = pd.DataFrame(calculo_x10_ie)
    
    print(f"   Instituciones con X10_IE calculado: {len(df_calculados)}")
    print(f"   X10_IE promedio: {df_calculados['X10_IE'].mean():.3f}")
    print(f"   Rango X10_IE: {df_calculados['X10_IE'].min():.3f} - {df_calculados['X10_IE'].max():.3f}")
    
    # 4. Análisis por componentes
    print(f"\n4. ANÁLISIS POR COMPONENTES:")
    print(f"   Conectividad digital promedio: {df_calculados['conectividad_digital'].mean():.3f}")
    print(f"   Equipamiento tecnológico promedio: {df_calculados['equipamiento_tecnologico'].mean():.3f}")
    print(f"   Infraestructura eléctrica promedio: {df_calculados['infraestructura_electrica'].mean():.3f}")
    
    print(f"\n   Instituciones con internet: {(df_calculados['internet_operativo'] == 1.0).sum()}")
    print(f"   Instituciones con electricidad: {(df_calculados['tiene_electricidad'] == 1.0).sum()}")
    print(f"   Equipos promedio por institución: {df_calculados['equipos_total'].mean():.1f}")
    
    # 5. Imputación contextual
    print(f"\n5. IMPUTACIÓN CONTEXTUAL:")
    
    # Vincular con target para obtener contexto
    df_calculados_extended = df_target.merge(df_calculados, left_on='CODIGO_MODULAR', right_on='codigo_modular', how='left')
    
    instituciones_con_datos = df_calculados_extended['X10_IE'].notna().sum()
    instituciones_sin_datos = df_calculados_extended['X10_IE'].isna().sum()
    
    print(f"   Instituciones con datos: {instituciones_con_datos}")
    print(f"   Instituciones sin datos: {instituciones_sin_datos}")
    
    # Imputación por contexto de ruralidad
    if instituciones_con_datos > 0:
        # Por ruralidad (X2_TR)
        imputacion_por_ruralidad = df_calculados_extended.groupby('X2_TR')['X10_IE'].mean()
        
        print(f"   Imputación por ruralidad:")
        for ruralidad, x10_promedio in imputacion_por_ruralidad.items():
            if pd.notna(x10_promedio):
                print(f"     X2_TR {ruralidad}: X10_IE = {x10_promedio:.3f}")
        
        # Aplicar imputación
        for idx, row in df_calculados_extended.iterrows():
            if pd.isna(row['X10_IE']):
                ruralidad = row['X2_TR']
                if ruralidad in imputacion_por_ruralidad and pd.notna(imputacion_por_ruralidad[ruralidad]):
                    valor_imputado = imputacion_por_ruralidad[ruralidad]
                    metodo_imputacion = f'ruralidad_{ruralidad}'
                else:
                    # Fallback: promedio general
                    valor_imputado = df_calculados['X10_IE'].mean()
                    metodo_imputacion = 'promedio_general'
                
                # Agregar registro imputado
                df_calculados_extended.at[idx, 'X10_IE'] = round(valor_imputado, 4)
                df_calculados_extended.at[idx, 'fuente'] = 'imputacion_contextual'
                df_calculados_extended.at[idx, 'metodo'] = metodo_imputacion
        
        print(f"   Imputación completada para todas las instituciones")
    
    # 6. Estadísticas finales
    print(f"\n6. ESTADÍSTICAS FINALES:")
    total_final = len(df_calculados_extended)
    x10_promedio_final = df_calculados_extended['X10_IE'].mean()
    
    print(f"   Total instituciones: {total_final}")
    print(f"   X10_IE promedio final: {x10_promedio_final:.3f}")
    print(f"   Desviación estándar: {df_calculados_extended['X10_IE'].std():.3f}")
    
    # Distribución por rangos
    print(f"\n   Distribución por niveles infraestructura:")
    bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    labels = ['Muy Baja (0-0.2)', 'Baja (0.2-0.4)', 'Media (0.4-0.6)', 'Alta (0.6-0.8)', 'Muy Alta (0.8-1.0)']
    df_calculados_extended['nivel_infraestructura'] = pd.cut(df_calculados_extended['X10_IE'], bins=bins, labels=labels, include_lowest=True)
    
    distribucion = df_calculados_extended['nivel_infraestructura'].value_counts().sort_index()
    for nivel, cantidad in distribucion.items():
        porcentaje = cantidad/total_final*100
        print(f"     {nivel}: {cantidad} instituciones ({porcentaje:.1f}%)")
    
    # 7. Generar CSV preliminar
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"temp_data/x10_ie_preliminar_{timestamp}.csv"
    
    # Preparar datos para CSV
    df_resultado = df_calculados_extended[[
        'CODIGO_MODULAR', 'NOMBRE_INSTITUCION', 'NUMERO_FYA', 'X2_TR',
        'X10_IE', 'fuente', 'metodo', 'nivel_infraestructura'
    ]].copy()
    
    # Agregar componentes para instituciones con datos directos
    df_resultado = df_resultado.merge(
        df_calculados[['codigo_modular', 'conectividad_digital', 'equipamiento_tecnologico', 
                      'infraestructura_electrica', 'internet_operativo', 'equipos_total', 'tiene_electricidad']], 
        left_on='CODIGO_MODULAR', right_on='codigo_modular', how='left'
    )
    
    df_resultado = df_resultado.drop('codigo_modular', axis=1)
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df_resultado.to_csv(csv_path, index=False)
    
    print(f"\n7. CSV PRELIMINAR GENERADO: {csv_path}")
    
    # 8. Resumen de calidad
    print(f"\n8. EVALUACIÓN DE CALIDAD:")
    datos_directos = (df_resultado['fuente'] == 'conectividad_equipamiento').sum()
    datos_imputados = (df_resultado['fuente'] == 'imputacion_contextual').sum()
    
    print(f"   Datos directos: {datos_directos} instituciones ({datos_directos/total_final*100:.1f}%)")
    print(f"   Datos imputados: {datos_imputados} instituciones ({datos_imputados/total_final*100:.1f}%)")
    print(f"   Completitud: {total_final}/184 instituciones (100%)")
    
    # Coherencia metodológica
    coherencia_ruralidad = df_resultado.groupby('X2_TR')['X10_IE'].mean()
    print(f"\n   Coherencia por ruralidad (urbano debería > rural):")
    for ruralidad, x10_prom in coherencia_ruralidad.items():
        tipo_nombre = "Urbano" if ruralidad == 1 else "Rural"
        print(f"     {tipo_nombre} (X2_TR={ruralidad}): X10_IE promedio = {x10_prom:.3f}")
    
    conn.close()
    
    return csv_path, total_final, x10_promedio_final, datos_directos, datos_imputados

if __name__ == "__main__":
    csv_file, total, promedio, directos, imputados = calcular_x10_ie_preliminar()
    
    print(f"\n=== RESULTADO PRELIMINAR X10_IE ===")
    print(f"Archivo CSV: {csv_file}")
    print(f"Cobertura: {total}/184 instituciones (100%)")
    print(f"X10_IE promedio: {promedio:.3f}")
    print(f"Datos directos: {directos} ({directos/total*100:.1f}%)")
    print(f"Datos imputados: {imputados} ({imputados/total*100:.1f}%)")
    
    if directos >= 50:
        print(f"\n[CALIDAD BUENA] Suficientes datos directos para metodología robusta")
        print(f"[RECOMENDACIÓN] Proceder con integración a indices_metodologicos")
    else:
        print(f"\n[CALIDAD LIMITADA] Pocos datos directos, evaluar resultados")
        print(f"[RECOMENDACIÓN] Revisar distribución antes de integración")