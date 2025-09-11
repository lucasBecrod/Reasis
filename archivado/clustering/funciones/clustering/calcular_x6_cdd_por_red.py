"""
Script para calcular X6_CDD - Competencia Digital Docente por Red
Metodología de agregación por red con normalización de códigos

Autor: Proyecto Reasis  
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import re

def normalizar_codigo_red(codigo_red):
    """Normaliza códigos de red para compatibilidad"""
    if pd.isna(codigo_red):
        return None
    
    # Extraer solo el número de la red
    codigo_str = str(codigo_red).upper().strip()
    
    # Buscar patrones: "RER FA XX", "RER_FA_XX", "XX", etc.
    numeros = re.findall(r'\d+', codigo_str)
    if numeros:
        return numeros[-1]  # Tomar el último número encontrado
    
    return None

def calcular_x6_cdd_por_red():
    """
    Calcula X6_CDD usando competencia digital docente agregada por red:
    
    METODOLOGÍA:
    1. Agregar evaluaciones digitales por red (promedio escala 1-4)
    2. Asignar a todas las instituciones de cada red el promedio correspondiente  
    3. Para instituciones sin datos de red: imputación contextual
    4. Variable final en escala 1-4 (coherente con X4_IDD)
    """
    
    print("=== CALCULANDO X6_CDD COMPETENCIA DIGITAL DOCENTE ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Obtener instituciones target
    df_target = pd.read_sql_query("""
        SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION, NUMERO_FYA
        FROM indices_metodologicos
    """, conn)
    
    print(f"1. INSTITUCIONES TARGET: {len(df_target)}")
    
    # 2. Procesar datos de competencia digital por red
    print(f"\n2. PROCESANDO COMPETENCIA DIGITAL POR RED:")
    
    df_digital_raw = pd.read_sql_query("""
        SELECT 
            codigo_red,
            nombre_rer,
            nota_global_relativa_num as nivel_digital_1_4,
            puntuacion_texto,
            ambito,
            edad,
            sexo
        FROM competencia_digital_docentes
        WHERE nota_global_relativa_num IS NOT NULL
    """, conn)
    
    print(f"   Total evaluaciones digitales: {len(df_digital_raw)}")
    
    # Normalizar códigos de red
    df_digital_raw['red_normalizada'] = df_digital_raw['codigo_red'].apply(normalizar_codigo_red)
    df_digital_clean = df_digital_raw[df_digital_raw['red_normalizada'].notna()].copy()
    
    print(f"   Evaluaciones con código de red válido: {len(df_digital_clean)}")
    
    # Agregar por red
    cdd_por_red = df_digital_clean.groupby('red_normalizada').agg({
        'nivel_digital_1_4': ['mean', 'std', 'count'],
        'nombre_rer': 'first',
        'puntuacion_texto': 'mean'
    }).reset_index()
    
    # Simplificar nombres de columnas
    cdd_por_red.columns = [
        'red_codigo', 'X6_CDD_promedio', 'X6_CDD_std', 'num_evaluaciones', 
        'nombre_red', 'puntuacion_promedio'
    ]
    
    print(f"   Redes con datos de competencia digital: {len(cdd_por_red)}")
    print(f"\n   Competencia Digital Docente por red (escala 1-4):")
    for _, row in cdd_por_red.iterrows():
        print(f"     Red {row['red_codigo']}: X6_CDD={row['X6_CDD_promedio']:.2f} +/- {row['X6_CDD_std']:.2f}")
        print(f"       Evaluaciones: {row['num_evaluaciones']} docentes")
        print(f"       Nombre: {row['nombre_red']}")
    
    # 3. Asignar X6_CDD a instituciones por red
    print(f"\n3. ASIGNACION X6_CDD A INSTITUCIONES:")
    
    # Preparar mapeo red → X6_CDD
    mapeo_red_cdd = dict(zip(cdd_por_red['red_codigo'], cdd_por_red['X6_CDD_promedio']))
    
    vinculaciones_por_red = []
    instituciones_sin_red = []
    
    for _, row in df_target.iterrows():
        codigo_ie = row['CODIGO_MODULAR']
        numero_fya = row['NUMERO_FYA']
        
        if pd.notna(numero_fya):
            red_str = str(int(numero_fya))
            
            if red_str in mapeo_red_cdd:
                # Institución con datos de competencia digital
                vinculaciones_por_red.append({
                    'codigo_target': codigo_ie,
                    'X6_CDD': mapeo_red_cdd[red_str],
                    'red_origen': red_str,
                    'num_evaluaciones': cdd_por_red[cdd_por_red['red_codigo'] == red_str]['num_evaluaciones'].iloc[0],
                    'fuente': 'Competencia_Digital_Red',
                    'metodo': 'promedio_red_docentes'
                })
            else:
                # Red sin datos digitales
                instituciones_sin_red.append({
                    'codigo_target': codigo_ie,
                    'red_sin_datos': red_str,
                    'motivo': 'red_sin_evaluaciones_digitales'
                })
        else:
            # Institución sin número de red
            instituciones_sin_red.append({
                'codigo_target': codigo_ie,
                'red_sin_datos': None,
                'motivo': 'institucion_sin_numero_red'
            })
    
    print(f"   Instituciones con X6_CDD desde red: {len(vinculaciones_por_red)}")
    print(f"   Instituciones sin datos de red: {len(instituciones_sin_red)}")
    
    # Mostrar cobertura por red
    if len(vinculaciones_por_red) > 0:
        cobertura_por_red = pd.DataFrame(vinculaciones_por_red).groupby('red_origen').agg({
            'codigo_target': 'count',
            'X6_CDD': 'first',
            'num_evaluaciones': 'first'
        }).reset_index()
        cobertura_por_red.columns = ['red', 'instituciones_cubiertas', 'X6_CDD', 'evaluaciones_base']
        
        print(f"\n   Cobertura por red:")
        for _, row in cobertura_por_red.iterrows():
            print(f"     Red {row['red']}: {row['instituciones_cubiertas']} instituciones -> X6_CDD {row['X6_CDD']:.2f}")
            print(f"       Base: {row['evaluaciones_base']} evaluaciones docentes")
    
    # 4. Imputación contextual para instituciones sin datos
    print(f"\n4. IMPUTACION CONTEXTUAL:")
    
    if len(vinculaciones_por_red) > 0:
        # Calcular promedio ponderado de redes disponibles
        valores_cdd = [v['X6_CDD'] for v in vinculaciones_por_red]
        evaluaciones_peso = [v['num_evaluaciones'] for v in vinculaciones_por_red]
        
        # Promedio ponderado por número de evaluaciones
        promedio_ponderado = np.average(valores_cdd, weights=evaluaciones_peso)
        promedio_simple = np.mean(valores_cdd)
        
        print(f"   Estadísticas para imputación:")
        print(f"     Promedio simple: {promedio_simple:.2f}")
        print(f"     Promedio ponderado: {promedio_ponderado:.2f}")
        print(f"     Rango disponible: {min(valores_cdd):.2f} - {max(valores_cdd):.2f}")
        
        valor_imputacion = promedio_ponderado
    else:
        # Fallback si no hay datos
        valor_imputacion = 2.0  # Nivel "En Proceso" por defecto
        print(f"   Sin datos disponibles - usando valor por defecto: {valor_imputacion}")
    
    # Crear vinculaciones imputadas
    vinculaciones_imputadas = []
    for inst in instituciones_sin_red:
        vinculaciones_imputadas.append({
            'codigo_target': inst['codigo_target'],
            'X6_CDD': valor_imputacion,
            'red_origen': inst.get('red_sin_datos', 'Sin_Red'),
            'num_evaluaciones': 0,
            'fuente': 'Imputacion_Contextual',
            'metodo': 'promedio_ponderado_redes'
        })
    
    print(f"   Instituciones imputadas: {len(vinculaciones_imputadas)}")
    print(f"   Valor de imputación: {valor_imputacion:.2f}")
    
    # 5. Consolidar resultados finales
    print(f"\n5. CONSOLIDACION FINAL:")
    
    todas_vinculaciones = vinculaciones_por_red + vinculaciones_imputadas
    
    print(f"   Total instituciones: {len(todas_vinculaciones)}")
    print(f"   Cobertura: {len(todas_vinculaciones)}/{len(df_target)} ({len(todas_vinculaciones)/len(df_target)*100:.1f}%)")
    
    # Distribución por fuente
    print(f"\n   Distribución por fuente:")
    df_resultado = pd.DataFrame(todas_vinculaciones)
    
    for fuente, grupo in df_resultado.groupby('fuente'):
        count = len(grupo)
        promedio = grupo['X6_CDD'].mean()
        print(f"     {fuente}: {count} instituciones (X6_CDD prom: {promedio:.2f})")
    
    # Estadísticas finales
    print(f"\n   Estadísticas X6_CDD:")
    print(f"     Rango: {df_resultado['X6_CDD'].min():.2f} - {df_resultado['X6_CDD'].max():.2f}")
    print(f"     Promedio: {df_resultado['X6_CDD'].mean():.2f}")
    print(f"     Mediana: {df_resultado['X6_CDD'].median():.2f}")
    
    # Distribución por niveles
    print(f"\n   Distribución por nivel de competencia:")
    for nivel_min, nivel_max, nombre in [(1.0, 1.99, 'Básico'), (2.0, 2.99, 'En Proceso'), (3.0, 3.99, 'Esperado'), (4.0, 4.0, 'Destacado')]:
        count = len(df_resultado[(df_resultado['X6_CDD'] >= nivel_min) & (df_resultado['X6_CDD'] <= nivel_max)])
        pct = count/len(df_resultado)*100
        print(f"     {nombre} ({nivel_min}-{nivel_max}): {count} instituciones ({pct:.1f}%)")
    
    # 6. Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"temp_data/x6_cdd_por_red_{timestamp}.csv"
    
    df_resultado.to_csv(csv_path, index=False)
    
    print(f"\n6. RESULTADOS GUARDADOS: {csv_path}")
    
    conn.close()
    
    return csv_path, len(df_resultado), df_resultado['X6_CDD'].mean()

if __name__ == "__main__":
    csv_file, total, promedio_cdd = calcular_x6_cdd_por_red()
    
    print(f"\n=== RESULTADO X6_CDD ===")
    print(f"Cobertura: {total}/184 instituciones")
    print(f"Promedio CDD (1-4): {promedio_cdd:.2f}")
    print(f"Archivo: {csv_file}")
    
    if total == 184:
        print(f"\n[EXITO] X6_CDD calculado para todas las instituciones")
        print(f"[METODOLOGIA] Agregación por red + Imputación ponderada")
    else:
        print(f"\n[PARCIAL] X6_CDD calculado - verificar cobertura")