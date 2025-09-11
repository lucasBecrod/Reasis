#!/usr/bin/env python3
"""
Resumen definitivo del análisis de valores NULL
"""

import sqlite3
import pandas as pd

def resumen_ejecutivo_nulls():
    """Generar resumen ejecutivo final"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("=" * 80)
    print("RESUMEN EJECUTIVO: ANÁLISIS DE VALORES NULL - REASIS DATABASE V4")
    print("=" * 80)
    
    # Datos principales
    df_ie = pd.read_sql_query("SELECT codigo_modular, nombre_institucion, numero_fya, entra_estudio_clustering FROM instituciones_educativas", conn)
    df_ie_completa = pd.read_sql_query("SELECT * FROM instituciones_educativas", conn)
    df_indices = pd.read_sql_query("SELECT CODIGO_MODULAR FROM indices_metodologicos", conn)
    
    # Calcular completitud
    null_counts = df_ie_completa.isnull().sum(axis=1)
    total_cols = len(df_ie_completa.columns)
    null_percentage = (null_counts / total_cols) * 100
    
    # 1. IDENTIFICACIÓN DE IIEE PROBLEMÁTICAS
    print("\n1. IIEE CON VALORES NULL IDENTIFICADAS:")
    print("   ========================================")
    
    muy_problematicas_idx = null_percentage > 80
    medias_problematicas_idx = (null_percentage > 15) & (null_percentage <= 80)
    
    muy_problematicas = df_ie[muy_problematicas_idx]
    medias_problematicas = df_ie[medias_problematicas_idx]
    
    print(f"   - TOTAL INSTITUCIONES: {len(df_ie)}")
    print(f"   - MUY PROBLEMÁTICAS (>80% NULL): {len(muy_problematicas)}")
    print(f"   - PROBLEMÁTICAS MEDIAS (15-80% NULL): {len(medias_problematicas)}")
    
    # 2. CÓDIGOS MODULARES ESPECÍFICOS
    print(f"\n2. CÓDIGOS MODULARES ESPECÍFICOS:")
    print("   ================================")
    
    print(f"\n   MUY PROBLEMÁTICAS (>80% NULL):")
    for idx, row in muy_problematicas.iterrows():
        codigo = row['codigo_modular']
        clustering = row['entra_estudio_clustering']
        idx_original = df_ie[df_ie['codigo_modular'] == codigo].index[0]
        pct_null = null_percentage.iloc[idx_original]
        print(f"     - CÓDIGO: {codigo}")
        print(f"       NULL: {pct_null:.1f}% | Clustering: {clustering if pd.notna(clustering) else 'NO DEFINIDO'}")
    
    print(f"\n   PROBLEMÁTICAS MEDIAS (15-80% NULL):")
    for idx, row in medias_problematicas.iterrows():
        codigo = row['codigo_modular']
        clustering = row['entra_estudio_clustering']
        idx_original = df_ie[df_ie['codigo_modular'] == codigo].index[0]
        pct_null = null_percentage.iloc[idx_original]
        print(f"     - CÓDIGO: {codigo}")
        print(f"       NULL: {pct_null:.1f}% | Clustering: {clustering if pd.notna(clustering) else 'NO'}")
    
    # 3. COLUMNAS MÁS AFECTADAS
    print(f"\n3. COLUMNAS MÁS AFECTADAS:")
    print("   ========================")
    
    null_by_column = df_ie_completa.isnull().sum()
    null_percentage_col = (null_by_column / len(df_ie_completa)) * 100
    cols_con_null = null_by_column[null_by_column > 0].sort_values(ascending=False)
    
    print(f"   Top 10 columnas con más valores NULL:")
    for i, (col, nulls) in enumerate(cols_con_null.head(10).items()):
        pct = null_percentage_col[col]
        completos = len(df_ie_completa) - nulls
        print(f"     {i+1:2d}. {col:35} | NULL: {nulls:3d} ({pct:5.1f}%) | OK: {completos:3d}")
    
    # 4. COMPARACIÓN CON INDICES_METODOLOGICOS
    print(f"\n4. COMPARACIÓN CON INDICES_METODOLOGICOS:")
    print("   =======================================")
    
    codigos_ie = set(df_ie['codigo_modular'])
    codigos_indices = set(df_indices['CODIGO_MODULAR'])
    
    muy_prob_codigos = set(muy_problematicas['codigo_modular'])
    medias_prob_codigos = set(medias_problematicas['codigo_modular'])
    
    muy_prob_en_indices = muy_prob_codigos & codigos_indices
    medias_prob_en_indices = medias_prob_codigos & codigos_indices
    
    print(f"   - Códigos en instituciones_educativas: {len(codigos_ie)}")
    print(f"   - Códigos en indices_metodologicos: {len(codigos_indices)}")
    print(f"   - MUY PROBLEMÁTICAS en indices: {len(muy_prob_en_indices)} de {len(muy_prob_codigos)}")
    print(f"   - PROBLEMÁTICAS MEDIAS en indices: {len(medias_prob_en_indices)} de {len(medias_prob_codigos)}")
    
    # 5. ESTADÍSTICAS DE COMPLETITUD
    print(f"\n5. ESTADÍSTICAS DE COMPLETITUD POR IIEE PROBLEMÁTICA:")
    print("   ===================================================")
    
    for idx, row in muy_problematicas.iterrows():
        codigo = row['codigo_modular']
        idx_original = df_ie_completa[df_ie_completa['codigo_modular'] == codigo].index[0]
        nulls = null_counts.iloc[idx_original]
        pct_null = null_percentage.iloc[idx_original]
        completas = total_cols - nulls
        pct_completo = 100 - pct_null
        
        print(f"   CÓDIGO {codigo}:")
        print(f"     - Columnas completas: {completas}/{total_cols} ({pct_completo:.1f}%)")
        print(f"     - Columnas NULL: {nulls}/{total_cols} ({pct_null:.1f}%)")
        
        # Mostrar cuáles columnas están completas
        fila = df_ie_completa.iloc[idx_original]
        cols_ok = fila[fila.notnull()].index.tolist()
        print(f"     - Campos OK: {', '.join(cols_ok[:6])}..." if len(cols_ok) > 6 else f"     - Campos OK: {', '.join(cols_ok)}")
    
    # 6. CONCLUSIONES Y RECOMENDACIONES
    print(f"\n6. CONCLUSIONES Y RECOMENDACIONES:")
    print("   =================================")
    
    print(f"   PROBLEMAS IDENTIFICADOS:")
    print(f"     - {len(muy_problematicas)} IIEE tienen >80% datos faltantes")
    print(f"     - {len(medias_problematicas)} IIEE tienen 15-80% datos faltantes") 
    print(f"     - 3 columnas tienen 100% valores NULL (no funcionales)")
    print(f"     - 2 columnas académicas tienen >50% valores NULL")
    
    print(f"\n   INSTITUCIONES QUE NECESITAN COMPLETAR DATOS:")
    todos_problematicos = list(muy_prob_codigos) + list(medias_prob_codigos)
    print(f"     - Códigos a priorizar: {', '.join(map(str, sorted(todos_problematicos)))}")
    
    print(f"\n   RECOMENDACIONES:")
    print(f"     1. URGENTE: Completar datos de códigos {', '.join(map(str, sorted(muy_prob_codigos)))}")
    print(f"     2. IMPORTANTE: Revisar códigos {', '.join(map(str, sorted(medias_prob_codigos)))}")
    print(f"     3. LIMPIEZA: Eliminar columnas 100% NULL no funcionales")
    print(f"     4. VALIDACIÓN: Verificar integridad de datos académicos Y3_PR")
    
    conn.close()

if __name__ == "__main__":
    resumen_ejecutivo_nulls()