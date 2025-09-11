"""
Script para calcular Y3_PR - Progreso Relativo (Desempeño Académico)

Calcula porcentajes de estudiantes en nivel satisfactorio por institución educativa
en tres materias: Comunicación, Matemática y Producción de textos

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

def calcular_y3_pr_progreso_relativo():
    """
    Calcula Y3_PR basado en porcentajes de estudiantes con nivel satisfactorio
    
    METODOLOGÍA:
    1. Agrupar evaluaciones por institución y materia
    2. Calcular % estudiantes con nivel 'Satisfactorio', 'Logrado' o 'Destacado'
    3. Crear índice compuesto promediando las tres materias
    4. Escala 0-100% (porcentaje directo)
    """
    
    print("=== CALCULANDO Y3_PR - PROGRESO RELATIVO ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Obtener instituciones target
    df_target = pd.read_sql_query("""
        SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION
        FROM indices_metodologicos
    """, conn)
    
    print(f"1. INSTITUCIONES TARGET: {len(df_target)}")
    
    # 2. Calcular porcentajes por materia e institución
    print(f"\n2. CALCULANDO PORCENTAJES POR MATERIA:")
    
    query_porcentajes = """
    SELECT 
        codigo_modular,
        materia,
        COUNT(*) as total_estudiantes,
        SUM(CASE WHEN nivel_logro_texto IN ('Satisfactorio', 'Logrado', 'Destacado') 
            THEN 1 ELSE 0 END) as estudiantes_satisfactorio,
        ROUND(SUM(CASE WHEN nivel_logro_texto IN ('Satisfactorio', 'Logrado', 'Destacado') 
                  THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as pct_satisfactorio
    FROM resultados_academicos
    WHERE materia IN ('Comunicación', 'Matemática', 'Producción de textos')
    GROUP BY codigo_modular, materia
    HAVING COUNT(*) >= 3  -- Mínimo 3 estudiantes evaluados por confiabilidad
    ORDER BY codigo_modular, materia
    """
    
    df_porcentajes = pd.read_sql_query(query_porcentajes, conn)
    
    print(f"   Instituciones con datos académicos: {df_porcentajes['codigo_modular'].nunique()}")
    print(f"   Registros materia-institución: {len(df_porcentajes)}")
    
    # Distribución por materia
    print(f"\n   Distribución por materia:")
    for materia in ['Comunicación', 'Matemática', 'Producción de textos']:
        subset = df_porcentajes[df_porcentajes['materia'] == materia]
        if len(subset) > 0:
            promedio = subset['pct_satisfactorio'].mean()
            instituciones = len(subset)
            print(f"     {materia}: {instituciones} instituciones - promedio {promedio:.2f}%")
    
    # 3. Crear matriz de materias por institución
    print(f"\n3. CONSTRUYENDO MATRIZ INSTITUCIONES x MATERIAS:")
    
    # Pivotar para tener una fila por institución
    df_pivot = df_porcentajes.pivot(index='codigo_modular', 
                                   columns='materia', 
                                   values='pct_satisfactorio').reset_index()
    
    # Renombrar columnas
    df_pivot.columns.name = None
    columnas_nuevas = {'codigo_modular': 'codigo_modular'}
    for col in df_pivot.columns:
        if col == 'Comunicación':
            columnas_nuevas[col] = 'comunicacion_pct'
        elif col == 'Matemática':
            columnas_nuevas[col] = 'matematica_pct'
        elif col == 'Producción de textos':
            columnas_nuevas[col] = 'produccion_textos_pct'
    
    df_pivot = df_pivot.rename(columns=columnas_nuevas)
    
    print(f"   Instituciones en matriz: {len(df_pivot)}")
    
    # 4. Calcular Y3_PR como promedio de las tres materias
    print(f"\n4. CALCULANDO Y3_PR COMPUESTO:")
    
    # Rellenar NaN con 0 para instituciones sin datos de alguna materia
    materias_cols = ['comunicacion_pct', 'matematica_pct', 'produccion_textos_pct']
    df_pivot[materias_cols] = df_pivot[materias_cols].fillna(0)
    
    # Calcular Y3_PR como promedio ponderado (solo materias con datos)
    def calcular_y3pr_promedio(row):
        valores = []
        if pd.notna(row['comunicacion_pct']) and row['comunicacion_pct'] > 0:
            valores.append(row['comunicacion_pct'])
        if pd.notna(row['matematica_pct']) and row['matematica_pct'] > 0:
            valores.append(row['matematica_pct'])
        if pd.notna(row['produccion_textos_pct']) and row['produccion_textos_pct'] > 0:
            valores.append(row['produccion_textos_pct'])
        
        if len(valores) > 0:
            return np.mean(valores)
        else:
            return np.nan
    
    # Calcular número de materias con datos
    df_pivot['num_materias_con_datos'] = (
        (df_pivot['comunicacion_pct'] > 0).astype(int) +
        (df_pivot['matematica_pct'] > 0).astype(int) +
        (df_pivot['produccion_textos_pct'] > 0).astype(int)
    )
    
    # Calcular Y3_PR
    df_pivot['Y3_PR'] = df_pivot.apply(calcular_y3pr_promedio, axis=1)
    
    # Estadísticas
    instituciones_con_y3pr = df_pivot[df_pivot['Y3_PR'].notna()]
    print(f"   Instituciones con Y3_PR: {len(instituciones_con_y3pr)}")
    print(f"   Rango Y3_PR: {instituciones_con_y3pr['Y3_PR'].min():.2f} - {instituciones_con_y3pr['Y3_PR'].max():.2f}")
    print(f"   Promedio Y3_PR: {instituciones_con_y3pr['Y3_PR'].mean():.2f}")
    
    # Distribución por número de materias
    print(f"\n   Distribución por materias evaluadas:")
    for n_materias in [1, 2, 3]:
        count = len(instituciones_con_y3pr[instituciones_con_y3pr['num_materias_con_datos'] == n_materias])
        if count > 0:
            promedio = instituciones_con_y3pr[instituciones_con_y3pr['num_materias_con_datos'] == n_materias]['Y3_PR'].mean()
            print(f"     {n_materias} materias: {count} instituciones - promedio {promedio:.2f}%")
    
    # 5. Guardar resultados temporales
    print(f"\n5. GUARDANDO RESULTADOS TEMPORALES:")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"temp_data/y3_pr_progreso_relativo_{timestamp}.csv"
    
    # Preparar datos para guardar
    df_resultado = df_pivot[['codigo_modular', 'comunicacion_pct', 'matematica_pct', 
                            'produccion_textos_pct', 'num_materias_con_datos', 'Y3_PR']].copy()
    
    df_resultado.to_csv(csv_path, index=False)
    print(f"   Archivo guardado: {csv_path}")
    
    # 6. Validación metodológica
    print(f"\n6. VALIDACIÓN METODOLÓGICA:")
    
    # Verificar distribución por rangos de desempeño
    print(f"   Distribución por rangos de desempeño:")
    if len(instituciones_con_y3pr) > 0:
        rangos = [
            (0, 2.99, "Muy Bajo (0-3%)"),
            (3, 5.99, "Bajo (3-6%)"), 
            (6, 9.99, "Medio-Bajo (6-10%)"),
            (10, 14.99, "Medio (10-15%)"),
            (15, 100, "Alto (>15%)")
        ]
        
        for min_val, max_val, nombre in rangos:
            count = len(instituciones_con_y3pr[
                (instituciones_con_y3pr['Y3_PR'] >= min_val) & 
                (instituciones_con_y3pr['Y3_PR'] < max_val)
            ])
            pct = count / len(instituciones_con_y3pr) * 100
            print(f"     {nombre}: {count} instituciones ({pct:.1f}%)")
    
    # Correlación con otras variables (si disponibles)
    print(f"\n   Validación cruzada con otras variables:")
    try:
        correlacion_query = """
        SELECT 
            i.CODIGO_MODULAR,
            i.Y1_ILA,
            i.Y2_TD,
            i.X4_IDD
        FROM indices_metodologicos i
        WHERE i.CODIGO_MODULAR IN ({})
        """.format(','.join([f"'{code}'" for code in instituciones_con_y3pr['codigo_modular']]))
        
        df_correlacion = pd.read_sql_query(correlacion_query, conn)
        df_merged = df_correlacion.merge(
            instituciones_con_y3pr[['codigo_modular', 'Y3_PR']], 
            left_on='CODIGO_MODULAR', 
            right_on='codigo_modular'
        )
        
        # Calcular correlaciones
        if len(df_merged) > 10:  # Mínimo para correlación confiable
            corr_y1 = df_merged[['Y3_PR', 'Y1_ILA']].dropna().corr().iloc[0,1]
            corr_y2 = df_merged[['Y3_PR', 'Y2_TD']].dropna().corr().iloc[0,1]
            corr_x4 = df_merged[['Y3_PR', 'X4_IDD']].dropna().corr().iloc[0,1]
            
            print(f"     Correlación Y3_PR vs Y1_ILA: {corr_y1:.3f}")
            print(f"     Correlación Y3_PR vs Y2_TD: {corr_y2:.3f}")
            print(f"     Correlación Y3_PR vs X4_IDD: {corr_x4:.3f}")
    except:
        print(f"     No se pudieron calcular correlaciones")
    
    conn.close()
    
    # 7. Evaluación de éxito
    cobertura_pct = len(instituciones_con_y3pr) / len(df_target) * 100
    
    print(f"\n7. EVALUACIÓN FINAL:")
    print(f"   Cobertura: {len(instituciones_con_y3pr)}/{len(df_target)} ({cobertura_pct:.1f}%)")
    print(f"   Promedio Y3_PR: {instituciones_con_y3pr['Y3_PR'].mean():.2f}%")
    print(f"   Archivo temporal: {csv_path}")
    
    if cobertura_pct >= 40:  # Al menos 40% de instituciones
        print(f"\n[ÉXITO] Y3_PR calculado exitosamente - cobertura aceptable")
        return csv_path, len(instituciones_con_y3pr), instituciones_con_y3pr['Y3_PR'].mean()
    else:
        print(f"\n[REVISAR] Y3_PR calculado - cobertura baja, evaluar inclusión")
        return csv_path, len(instituciones_con_y3pr), instituciones_con_y3pr['Y3_PR'].mean()

if __name__ == "__main__":
    csv_file, total_con_datos, promedio_y3pr = calcular_y3_pr_progreso_relativo()
    
    print(f"\n=== RESULTADO Y3_PR ===")
    print(f"Instituciones con datos: {total_con_datos}")
    print(f"Promedio Progreso Relativo: {promedio_y3pr:.2f}%")
    print(f"Archivo: {csv_file}")
    
    if total_con_datos >= 75:  # Meta: 75+ instituciones
        print(f"\n[ÉXITO] Y3_PR listo para aplicar a índices_metodológicos")
    else:
        print(f"\n[PARCIAL] Y3_PR calculado - evaluar aplicación")