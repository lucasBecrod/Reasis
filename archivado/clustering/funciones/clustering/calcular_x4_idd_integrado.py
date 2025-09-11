"""
Script para calcular X4_IDD - Índice Desempeño Docente INTEGRADO
Combina datos PADD + Competencia Digital Docentes

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

def calcular_x4_idd_integrado():
    """
    Calcula X4_IDD usando metodología integrada:
    
    METODOLOGÍA DE INTEGRACIÓN:
    1. NIVEL 1 - PADD Individual: Para docentes con 4 notas PADD completas
       IDD_PADD = (nota_matematica + nota_comunicacion + nota_digital + nota_genero) / 4
    
    2. NIVEL 2 - Competencia Digital: Para instituciones sin PADD pero con evaluación digital
       IDD_DIGITAL = puntuacion_texto (normalizada a escala 0-20)
    
    3. NIVEL 3 - Agregación Institucional:
       X4_IDD = Promedio IDD de todos los docentes por institución
    
    4. NIVEL 4 - Imputación Contextual:
       Para instituciones sin datos: X4_IDD basado en promedio por red/contexto
    """
    
    print("=== CALCULANDO X4_IDD INTEGRADO ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Obtener instituciones target
    df_target = pd.read_sql_query("""
        SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION, NUMERO_FYA
        FROM indices_metodologicos
    """, conn)
    
    print(f"1. INSTITUCIONES TARGET: {len(df_target)}")
    
    # 2. NIVEL 1: Datos PADD individuales
    print(f"\n2. PROCESANDO DATOS PADD:")
    
    df_padd = pd.read_sql_query("""
        SELECT 
            printf('%07s', codigo_modular_actual) as codigo_ie,
            dni,
            nombre_completo,
            nota_matematica,
            nota_comunicacion, 
            nota_digital,
            nota_genero,
            rer
        FROM docentes_data
        WHERE codigo_modular_actual IS NOT NULL
          AND nota_matematica IS NOT NULL 
          AND nota_comunicacion IS NOT NULL
          AND nota_digital IS NOT NULL
          AND nota_genero IS NOT NULL
    """, conn)
    
    print(f"   Docentes con evaluación PADD completa: {len(df_padd)}")
    
    # Calcular IDD individual PADD
    df_padd['IDD_PADD'] = (
        df_padd['nota_matematica'].astype(float) +
        df_padd['nota_comunicacion'].astype(float) + 
        df_padd['nota_digital'].astype(float) +
        df_padd['nota_genero'].astype(float)
    ) / 4
    
    print(f"   Rango IDD_PADD: {df_padd['IDD_PADD'].min():.1f} - {df_padd['IDD_PADD'].max():.1f}")
    print(f"   Promedio IDD_PADD: {df_padd['IDD_PADD'].mean():.1f}")
    
    # 3. NIVEL 2: Datos Competencia Digital
    print(f"\n3. PROCESANDO COMPETENCIA DIGITAL:")
    
    df_digital = pd.read_sql_query("""
        SELECT 
            nombre_rer,
            codigo_red,
            puntuacion_texto,
            nota_global_relativa_num,
            ambito
        FROM competencia_digital_docentes
        WHERE puntuacion_texto IS NOT NULL
    """, conn)
    
    print(f"   Evaluaciones digitales disponibles: {len(df_digital)}")
    
    # Normalizar puntuación digital a escala 0-20 (como PADD)
    puntuacion_min = df_digital['puntuacion_texto'].min()
    puntuacion_max = df_digital['puntuacion_texto'].max()
    
    df_digital['IDD_DIGITAL'] = (
        (df_digital['puntuacion_texto'] - puntuacion_min) / 
        (puntuacion_max - puntuacion_min)
    ) * 20
    
    print(f"   Puntuación digital original: {puntuacion_min} - {puntuacion_max}")
    print(f"   IDD_DIGITAL normalizado: {df_digital['IDD_DIGITAL'].min():.1f} - {df_digital['IDD_DIGITAL'].max():.1f}")
    
    # Promedio por red
    digital_por_red = df_digital.groupby('codigo_red').agg({
        'IDD_DIGITAL': 'mean',
        'puntuacion_texto': 'count'
    }).reset_index()
    digital_por_red.columns = ['codigo_red', 'IDD_DIGITAL_promedio', 'num_evaluaciones']
    
    print(f"   Redes con datos digitales: {len(digital_por_red)}")
    for _, row in digital_por_red.iterrows():
        print(f"     Red {row['codigo_red']}: IDD={row['IDD_DIGITAL_promedio']:.1f} ({row['num_evaluaciones']} evaluaciones)")
    
    # 4. NIVEL 3: Agregación por institución
    print(f"\n4. AGREGACION POR INSTITUCION:")
    
    # 4a. Instituciones con datos PADD
    idd_padd_ie = df_padd.groupby('codigo_ie').agg({
        'IDD_PADD': 'mean',
        'dni': 'count'
    }).reset_index()
    idd_padd_ie.columns = ['codigo_target', 'X4_IDD', 'num_docentes_padd']
    idd_padd_ie['fuente'] = 'PADD'
    idd_padd_ie['metodo'] = 'promedio_docentes_padd'
    
    print(f"   Instituciones con IDD desde PADD: {len(idd_padd_ie)}")
    
    # 4b. Instituciones con datos digitales (para las que no tienen PADD)
    # Mapear redes a instituciones
    mapeo_red_ie = pd.read_sql_query("""
        SELECT CODIGO_MODULAR, NUMERO_FYA
        FROM indices_metodologicos
        WHERE NUMERO_FYA IS NOT NULL
    """, conn)
    
    # Vincular con competencia digital
    idd_digital_ie = []
    codigos_ya_con_padd = set(idd_padd_ie['codigo_target'])
    
    for _, row in mapeo_red_ie.iterrows():
        codigo_ie = row['CODIGO_MODULAR']
        red_fya = str(row['NUMERO_FYA'])
        
        if codigo_ie not in codigos_ya_con_padd:  # Solo si no tiene datos PADD
            # Buscar datos digitales para esta red
            digital_red = digital_por_red[digital_por_red['codigo_red'] == red_fya]
            if len(digital_red) > 0:
                idd_digital_ie.append({
                    'codigo_target': codigo_ie,
                    'X4_IDD': digital_red['IDD_DIGITAL_promedio'].iloc[0],
                    'num_evaluaciones_digital': digital_red['num_evaluaciones'].iloc[0],
                    'fuente': 'Competencia_Digital',
                    'metodo': 'promedio_red_digital'
                })
    
    df_idd_digital = pd.DataFrame(idd_digital_ie)
    print(f"   Instituciones con IDD desde Digital: {len(df_idd_digital)}")
    
    # 5. NIVEL 4: Imputación contextual
    print(f"\n5. IMPUTACION CONTEXTUAL:")
    
    codigos_con_datos = set(idd_padd_ie['codigo_target']) | set(df_idd_digital['codigo_target'] if len(df_idd_digital) > 0 else [])
    instituciones_sin_datos = df_target[~df_target['CODIGO_MODULAR'].isin(codigos_con_datos)]
    
    print(f"   Instituciones sin datos IDD: {len(instituciones_sin_datos)}")
    
    # Calcular promedio general para imputación
    if len(idd_padd_ie) > 0:
        promedio_padd = idd_padd_ie['X4_IDD'].mean()
    else:
        promedio_padd = 0
        
    if len(df_idd_digital) > 0:
        promedio_digital = df_idd_digital['X4_IDD'].mean()
    else:
        promedio_digital = 0
    
    # Promedio ponderado basado en cantidad de datos
    if len(idd_padd_ie) > 0 and len(df_idd_digital) > 0:
        peso_padd = len(idd_padd_ie) / (len(idd_padd_ie) + len(df_idd_digital))
        peso_digital = len(df_idd_digital) / (len(idd_padd_ie) + len(df_idd_digital))
        valor_imputacion = (promedio_padd * peso_padd) + (promedio_digital * peso_digital)
    elif len(idd_padd_ie) > 0:
        valor_imputacion = promedio_padd
    elif len(df_idd_digital) > 0:
        valor_imputacion = promedio_digital
    else:
        valor_imputacion = 13.0  # Valor por defecto basado en experiencia educativa
    
    print(f"   Valor para imputación: {valor_imputacion:.1f}")
    print(f"     Basado en: PADD prom={promedio_padd:.1f}, Digital prom={promedio_digital:.1f}")
    
    # Crear registros imputados
    idd_imputadas = []
    for _, row in instituciones_sin_datos.iterrows():
        idd_imputadas.append({
            'codigo_target': row['CODIGO_MODULAR'],
            'X4_IDD': valor_imputacion,
            'fuente': 'Imputacion_Contextual',
            'metodo': 'promedio_ponderado_general'
        })
    
    df_idd_imputadas = pd.DataFrame(idd_imputadas)
    
    # 6. Consolidar todas las fuentes
    print(f"\n6. CONSOLIDACION FINAL:")
    
    # Combinar todos los datos - Solo 1 registro por institución
    todas_fuentes = {}
    
    # PADD (Prioridad 1)
    for _, row in idd_padd_ie.iterrows():
        codigo = row['codigo_target']
        todas_fuentes[codigo] = {
            'codigo_target': codigo,
            'X4_IDD': row['X4_IDD'],
            'fuente': row['fuente'],
            'metodo': row['metodo'],
            'num_docentes': row['num_docentes_padd']
        }
    
    # Digital (Prioridad 2 - solo si no hay PADD)
    if len(df_idd_digital) > 0:
        for _, row in df_idd_digital.iterrows():
            codigo = row['codigo_target']
            if codigo not in todas_fuentes:  # Solo si no tiene PADD
                todas_fuentes[codigo] = {
                    'codigo_target': codigo,
                    'X4_IDD': row['X4_IDD'],
                    'fuente': row['fuente'],
                    'metodo': row['metodo'],
                    'num_docentes': row['num_evaluaciones_digital']
                }
    
    # Imputadas (Prioridad 3 - solo si no hay datos previos)
    for _, row in df_idd_imputadas.iterrows():
        codigo = row['codigo_target']
        if codigo not in todas_fuentes:  # Solo si no tiene datos previos
            todas_fuentes[codigo] = {
                'codigo_target': codigo,
                'X4_IDD': row['X4_IDD'],
                'fuente': row['fuente'],
                'metodo': row['metodo'],
                'num_docentes': 0
            }
    
    df_resultado = pd.DataFrame(list(todas_fuentes.values()))
    
    print(f"   Total vinculaciones: {len(df_resultado)}")
    print(f"   Cobertura: {len(df_resultado)}/{len(df_target)} ({len(df_resultado)/len(df_target)*100:.1f}%)")
    
    # Distribución por fuente
    print(f"\n   Distribución por fuente:")
    for fuente, grupo in df_resultado.groupby('fuente'):
        count = len(grupo)
        promedio = grupo['X4_IDD'].mean()
        print(f"     {fuente}: {count} instituciones (IDD prom: {promedio:.1f})")
    
    # Estadísticas finales
    print(f"\n   Estadísticas X4_IDD:")
    print(f"     Rango: {df_resultado['X4_IDD'].min():.1f} - {df_resultado['X4_IDD'].max():.1f}")
    print(f"     Promedio: {df_resultado['X4_IDD'].mean():.1f}")
    print(f"     Mediana: {df_resultado['X4_IDD'].median():.1f}")
    
    # 7. Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"temp_data/x4_idd_integrado_{timestamp}.csv"
    
    df_resultado.to_csv(csv_path, index=False)
    
    print(f"\n7. RESULTADOS GUARDADOS: {csv_path}")
    
    conn.close()
    
    return csv_path, len(df_resultado), df_resultado['X4_IDD'].mean()

if __name__ == "__main__":
    csv_file, total, promedio_idd = calcular_x4_idd_integrado()
    
    print(f"\n=== RESULTADO X4_IDD INTEGRADO ===")
    print(f"Cobertura: {total}/184 instituciones")
    print(f"Promedio IDD: {promedio_idd:.1f}")
    print(f"Archivo: {csv_file}")
    
    if total == 184:
        print(f"\n[EXITO] X4_IDD calculado para todas las instituciones")
        print(f"[METODOLOGIA] Integración exitosa PADD + Competencia Digital + Imputación")
    else:
        print(f"\n[PARCIAL] X4_IDD calculado - verificar cobertura")