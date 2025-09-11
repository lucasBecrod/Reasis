#!/usr/bin/env python3
"""
Análisis detallado de valores NULL en base de datos Reasis
Identifica IIEE con problemas de completitud de datos
"""

import sqlite3
import pandas as pd
import numpy as np

def conectar_db():
    """Conectar a base de datos"""
    return sqlite3.connect('reasis_database_v4.db')

def analizar_nulls_instituciones():
    """Analizar valores NULL en tabla instituciones_educativas"""
    
    conn = conectar_db()
    
    # Cargar tabla completa
    print("=== ANÁLISIS DE VALORES NULL EN INSTITUCIONES_EDUCATIVAS ===\n")
    
    df_ie = pd.read_sql_query("SELECT * FROM instituciones_educativas", conn)
    print(f"Total instituciones: {len(df_ie)}")
    print(f"Total columnas: {len(df_ie.columns)}\n")
    
    # Calcular porcentaje de NULL por institución
    null_counts = df_ie.isnull().sum(axis=1)
    total_cols = len(df_ie.columns)
    null_percentage = (null_counts / total_cols) * 100
    
    # Agregar información de NULL al dataframe
    df_analysis = df_ie[['codigo_modular', 'nombre_institucion']].copy()
    df_analysis['columnas_null'] = null_counts
    df_analysis['porcentaje_null'] = null_percentage
    df_analysis['columnas_completas'] = total_cols - null_counts
    df_analysis['porcentaje_completo'] = 100 - null_percentage
    
    # Ordenar por mayor porcentaje de NULL
    df_analysis = df_analysis.sort_values('porcentaje_null', ascending=False)
    
    print("=== TOP 20 IIEE CON MÁS VALORES NULL ===")
    top_nulls = df_analysis.head(20)
    for idx, row in top_nulls.iterrows():
        print(f"Código: {row['codigo_modular']} | NULL: {row['columnas_null']}/{total_cols} ({row['porcentaje_null']:.1f}%) | Completas: {row['columnas_completas']} ({row['porcentaje_completo']:.1f}%)")
        print(f"  Nombre: {row['nombre_institucion']}")
        print()
    
    # Estadísticas generales
    print("=== ESTADÍSTICAS GENERALES DE COMPLETITUD ===")
    print(f"Promedio columnas NULL por IIEE: {null_counts.mean():.1f}")
    print(f"Promedio porcentaje NULL: {null_percentage.mean():.1f}%")
    print(f"IIEE con >50% NULL: {len(df_analysis[df_analysis['porcentaje_null'] > 50])}")
    print(f"IIEE con >70% NULL: {len(df_analysis[df_analysis['porcentaje_null'] > 70])}")
    print(f"IIEE con >90% NULL: {len(df_analysis[df_analysis['porcentaje_null'] > 90])}\n")
    
    conn.close()
    return df_analysis

def analizar_nulls_por_columna():
    """Analizar qué columnas tienen más valores NULL"""
    
    conn = conectar_db()
    
    df_ie = pd.read_sql_query("SELECT * FROM instituciones_educativas", conn)
    
    print("=== COLUMNAS CON MÁS VALORES NULL ===")
    
    # Calcular NULL por columna
    null_by_column = df_ie.isnull().sum()
    total_rows = len(df_ie)
    null_percentage_col = (null_by_column / total_rows) * 100
    
    # Crear análisis por columna
    col_analysis = pd.DataFrame({
        'columna': null_by_column.index,
        'valores_null': null_by_column.values,
        'porcentaje_null': null_percentage_col.values,
        'valores_completos': total_rows - null_by_column.values
    }).sort_values('porcentaje_null', ascending=False)
    
    print("Top 15 columnas con más NULL:")
    for idx, row in col_analysis.head(15).iterrows():
        print(f"{row['columna']:30} | NULL: {row['valores_null']:3d} ({row['porcentaje_null']:5.1f}%) | Completos: {row['valores_completos']:3d}")
    
    conn.close()
    return col_analysis

def comparar_con_indices_metodologicos():
    """Comparar IIEE problemáticas con tabla indices_metodologicos"""
    
    conn = conectar_db()
    
    # Verificar si existe la tabla
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='indices_metodologicos'")
    if not cursor.fetchone():
        print("=== TABLA indices_metodologicos NO EXISTE ===\n")
        conn.close()
        return None
    
    print("=== COMPARACIÓN CON INDICES_METODOLOGICOS ===\n")
    
    # Cargar ambas tablas
    df_ie = pd.read_sql_query("SELECT codigo_modular FROM instituciones_educativas", conn)
    df_indices = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    
    print(f"IIEE en instituciones_educativas: {len(df_ie)}")
    print(f"IIEE en indices_metodologicos: {len(df_indices)}")
    
    # Verificar códigos que están en IE pero no en indices
    codigos_ie = set(df_ie['codigo_modular'])
    codigos_indices = set(df_indices['codigo_modular'])
    
    solo_en_ie = codigos_ie - codigos_indices
    solo_en_indices = codigos_indices - codigos_ie
    
    print(f"Códigos solo en instituciones_educativas: {len(solo_en_ie)}")
    print(f"Códigos solo en indices_metodologicos: {len(solo_en_indices)}")
    
    if solo_en_ie:
        print("\nCódigos modulares que están en IE pero NO en indices:")
        for codigo in sorted(solo_en_ie):
            print(f"  {codigo}")
    
    if solo_en_indices:
        print("\nCódigos modulares que están en indices pero NO en IE:")
        for codigo in sorted(solo_en_indices):
            print(f"  {codigo}")
    
    conn.close()
    return {
        'solo_en_ie': solo_en_ie,
        'solo_en_indices': solo_en_indices,
        'codigos_ie': codigos_ie,
        'codigos_indices': codigos_indices
    }

def identificar_iiee_problematicas():
    """Identificar IIEE específicas que necesitan completar datos"""
    
    conn = conectar_db()
    
    print("=== IDENTIFICACIÓN DE IIEE PROBLEMÁTICAS ===\n")
    
    df_ie = pd.read_sql_query("SELECT * FROM instituciones_educativas", conn)
    
    # Calcular completitud
    null_counts = df_ie.isnull().sum(axis=1)
    total_cols = len(df_ie.columns)
    null_percentage = (null_counts / total_cols) * 100
    
    # Filtrar IIEE con >60% NULL (criterio de problemáticas)
    problematicas_idx = null_percentage > 60
    df_problematicas = df_ie[problematicas_idx].copy()
    
    print(f"IIEE con >60% valores NULL: {len(df_problematicas)}")
    print("\nDetalle de IIEE problemáticas:")
    
    for idx in df_problematicas.index:
        codigo = df_ie.loc[idx, 'codigo_modular']
        nombre = df_ie.loc[idx, 'nombre_institucion']
        nulls = null_counts.iloc[idx]
        pct_null = null_percentage.iloc[idx]
        
        print(f"\nCódigo: {codigo}")
        print(f"Nombre: {nombre}")
        print(f"Columnas NULL: {nulls}/{total_cols} ({pct_null:.1f}%)")
        
        # Mostrar qué columnas específicas son NULL
        fila = df_ie.loc[idx]
        cols_null = fila[fila.isnull()].index.tolist()
        cols_completas = fila[fila.notnull()].index.tolist()
        
        print(f"Columnas COMPLETAS ({len(cols_completas)}): {', '.join(cols_completas[:10])}{'...' if len(cols_completas) > 10 else ''}")
        print(f"Columnas NULL ({len(cols_null)}): {', '.join(cols_null[:10])}{'...' if len(cols_null) > 10 else ''}")
    
    conn.close()
    return df_problematicas

def main():
    """Función principal"""
    
    print("ANÁLISIS DETALLADO DE VALORES NULL - REASIS DATABASE V4\n")
    print("=" * 70)
    
    try:
        # 1. Análisis de NULL por institución
        df_analysis = analizar_nulls_instituciones()
        
        print("=" * 70)
        
        # 2. Análisis de NULL por columna
        col_analysis = analizar_nulls_por_columna()
        
        print("\n" + "=" * 70)
        
        # 3. Comparación con indices_metodologicos
        comparacion = comparar_con_indices_metodologicos()
        
        print("=" * 70)
        
        # 4. Identificar IIEE problemáticas específicas
        problematicas = identificar_iiee_problematicas()
        
        print("\n" + "=" * 70)
        print("ANÁLISIS COMPLETADO")
        print(f"Revisar códigos modulares problemáticos identificados")
        
    except Exception as e:
        print(f"Error en análisis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()