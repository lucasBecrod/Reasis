"""
Script para expandir X5_ED usando múltiples fuentes de datos docentes
Combina datos de x5_ed_estabilidad_docente + docentes_data + instituciones_educativas

Autor: Proyecto Reasis
Fecha: 2025-08-10
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

def expandir_x5_ed_multifuente():
    """
    Expande X5_ED combinando todas las fuentes disponibles:
    1. x5_ed_estabilidad_docente (datos base)
    2. docentes_data (para inferir estabilidad por evaluaciones)
    3. instituciones_educativas (datos totales docentes)
    """
    
    print("=== EXPANDIENDO X5_ED MULTIFUENTE ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Datos base desde x5_ed_estabilidad_docente
    print("1. CARGANDO DATOS BASE X5_ED:")
    df_base = pd.read_sql_query("""
        SELECT codigo_modular, ratio_nombrados as X5_ED, 'x5_ed_tabla' as fuente
        FROM x5_ed_estabilidad_docente
    """, conn)
    print(f"   Datos base: {len(df_base)} instituciones")
    
    # 2. Calcular estabilidad desde docentes_data 
    print("\n2. CALCULANDO DESDE DOCENTES_DATA:")
    
    # Asumir que docentes con evaluaciones más recientes son más estables
    df_docentes_estabilidad = pd.read_sql_query("""
        SELECT 
            codigo_modular_vinculado as codigo_modular,
            COUNT(*) as total_evaluaciones,
            COUNT(CASE WHEN año = 2024 THEN 1 END) as eval_2024,
            COUNT(CASE WHEN año = 2023 THEN 1 END) as eval_2023,
            AVG(CASE 
                WHEN año = 2024 THEN 1.0
                WHEN año = 2023 THEN 0.8 
                ELSE 0.5 
            END) as indice_estabilidad
        FROM docentes_data 
        WHERE codigo_modular_vinculado IS NOT NULL
        GROUP BY codigo_modular_vinculado
    """, conn)
    
    # Normalizar índice_estabilidad a rango 0-1
    if len(df_docentes_estabilidad) > 0:
        df_docentes_estabilidad['X5_ED'] = df_docentes_estabilidad['indice_estabilidad']
        df_docentes_estabilidad['fuente'] = 'docentes_data'
        
        print(f"   Instituciones desde docentes_data: {len(df_docentes_estabilidad)}")
        print(f"   Rango estabilidad: {df_docentes_estabilidad['X5_ED'].min():.3f} - {df_docentes_estabilidad['X5_ED'].max():.3f}")
    
    # 3. Imputación por características institucionales
    print("\n3. IMPUTACION POR CARACTERISTICAS INSTITUCIONALES:")
    
    # Obtener instituciones sin X5_ED
    df_instituciones = pd.read_sql_query("""
        SELECT codigo_modular, total_docentes, es_rural, modalidad_especifica
        FROM instituciones_educativas
    """, conn)
    
    # Códigos ya cubiertos
    codigos_cubiertos = set(df_base['codigo_modular']).union(
        set(df_docentes_estabilidad['codigo_modular']) if len(df_docentes_estabilidad) > 0 else set()
    )
    
    # Instituciones faltantes
    df_faltantes = df_instituciones[~df_instituciones['codigo_modular'].isin(codigos_cubiertos)].copy()
    
    if len(df_faltantes) > 0:
        print(f"   Instituciones para imputar: {len(df_faltantes)}")
        
        # Imputación basada en características
        # Rural = menor estabilidad, urbano = mayor estabilidad
        df_faltantes['X5_ED'] = np.where(
            df_faltantes['es_rural'] == 1,
            0.35,  # Rural: estabilidad media-baja
            0.65   # Urbano: estabilidad media-alta
        )
        
        # Ajustar por tamaño (más docentes = más estabilidad)
        df_faltantes.loc[df_faltantes['total_docentes'] > 10, 'X5_ED'] += 0.1
        df_faltantes.loc[df_faltantes['total_docentes'] < 3, 'X5_ED'] -= 0.1
        
        # Mantener en rango [0, 1]
        df_faltantes['X5_ED'] = df_faltantes['X5_ED'].clip(0, 1)
        df_faltantes['fuente'] = 'imputacion_contextual'
        
        df_imputadas = df_faltantes[['codigo_modular', 'X5_ED', 'fuente']].copy()
        print(f"   Promedio imputado: {df_imputadas['X5_ED'].mean():.3f}")
    else:
        df_imputadas = pd.DataFrame(columns=['codigo_modular', 'X5_ED', 'fuente'])
    
    # 4. Consolidar todas las fuentes
    print("\n4. CONSOLIDANDO FUENTES:")
    
    df_consolidado = pd.concat([
        df_base,
        df_docentes_estabilidad[['codigo_modular', 'X5_ED', 'fuente']] if len(df_docentes_estabilidad) > 0 else pd.DataFrame(),
        df_imputadas
    ], ignore_index=True)
    
    # Eliminar duplicados (prioridad: base > docentes_data > imputacion)
    df_consolidado = df_consolidado.drop_duplicates(subset=['codigo_modular'], keep='first')
    
    print(f"   Total consolidado: {len(df_consolidado)} instituciones")
    
    # Distribución por fuente
    fuentes_dist = df_consolidado['fuente'].value_counts()
    for fuente, count in fuentes_dist.items():
        print(f"   {fuente}: {count} instituciones")
    
    # 5. Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = f"temp_data/x5_ed_expandido_{timestamp}.csv"
    df_consolidado.to_csv(csv_path, index=False)
    
    # 6. Estadísticas finales
    print(f"\n5. ESTADISTICAS FINALES:")
    print(f"   Cobertura: {len(df_consolidado)} instituciones")
    print(f"   Promedio X5_ED: {df_consolidado['X5_ED'].mean():.3f}")
    print(f"   Rango: {df_consolidado['X5_ED'].min():.3f} - {df_consolidado['X5_ED'].max():.3f}")
    
    # Distribución por rangos
    df_consolidado['rango'] = pd.cut(df_consolidado['X5_ED'], 
                                   bins=[0, 0.3, 0.7, 1.0], 
                                   labels=['Baja', 'Media', 'Alta'],
                                   include_lowest=True)
    
    print(f"\n   Distribución por estabilidad:")
    for rango, count in df_consolidado['rango'].value_counts().items():
        print(f"   {rango}: {count} instituciones")
    
    print(f"\n6. ARCHIVO CREADO: {csv_path}")
    
    conn.close()
    
    return csv_path, len(df_consolidado), df_consolidado['X5_ED'].mean()

if __name__ == "__main__":
    csv_file, total, promedio = expandir_x5_ed_multifuente()
    print(f"\n[RESULTADO] X5_ED expandido: {total} instituciones")
    print(f"[CALIDAD] Promedio estabilidad: {promedio:.3f}")
    print(f"[ARCHIVO] {csv_file}")