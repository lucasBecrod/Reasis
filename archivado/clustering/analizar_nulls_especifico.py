#!/usr/bin/env python3
"""
Análisis específico de IIEE con valores NULL problemáticas
"""

import sqlite3
import pandas as pd
import numpy as np

def analizar_iiee_problematicas_especifico():
    """Análisis detallado de las IIEE más problemáticas"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("=== ANÁLISIS ESPECÍFICO DE IIEE PROBLEMÁTICAS ===\n")
    
    # Cargar tabla instituciones_educativas
    df_ie = pd.read_sql_query("SELECT * FROM instituciones_educativas", conn)
    print(f"Total instituciones: {len(df_ie)}")
    print(f"Total columnas: {len(df_ie.columns)}\n")
    
    # Calcular completitud por institución
    null_counts = df_ie.isnull().sum(axis=1)
    total_cols = len(df_ie.columns)
    null_percentage = (null_counts / total_cols) * 100
    
    # Crear análisis detallado
    df_analysis = df_ie[['codigo_modular', 'nombre_institucion', 'numero_fya', 'entra_estudio_clustering']].copy()
    df_analysis['columnas_null'] = null_counts
    df_analysis['porcentaje_null'] = null_percentage
    df_analysis['columnas_completas'] = total_cols - null_counts
    
    # Ordenar por mayor porcentaje de NULL
    df_analysis = df_analysis.sort_values('porcentaje_null', ascending=False)
    
    print("=== TOP 15 IIEE MÁS PROBLEMÁTICAS (MÁS NULLS) ===")
    for idx, row in df_analysis.head(15).iterrows():
        print(f"Código: {row['codigo_modular']} | NULLs: {row['columnas_null']}/{total_cols} ({row['porcentaje_null']:.1f}%)")
        print(f"  Nombre: {row['nombre_institucion'] if pd.notna(row['nombre_institucion']) else 'SIN NOMBRE'}")
        print(f"  Número FyA: {row['numero_fya'] if pd.notna(row['numero_fya']) else 'NO DEFINIDO'}")
        print(f"  En clustering: {row['entra_estudio_clustering'] if pd.notna(row['entra_estudio_clustering']) else 'NO DEFINIDO'}")
        print()
    
    # Identificar las IIEE con >80% NULL (muy problemáticas)
    muy_problematicas = df_analysis[df_analysis['porcentaje_null'] > 80]
    print(f"=== IIEE CON >80% VALORES NULL (MUY PROBLEMÁTICAS): {len(muy_problematicas)} ===")
    
    if len(muy_problematicas) > 0:
        for idx, row in muy_problematicas.iterrows():
            codigo = row['codigo_modular']
            print(f"\n[CRITICO] CODIGO: {codigo}")
            print(f"   NULLs: {row['columnas_null']}/{total_cols} ({row['porcentaje_null']:.1f}%)")
            print(f"   Nombre: {row['nombre_institucion'] if pd.notna(row['nombre_institucion']) else 'SIN NOMBRE'}")
            
            # Mostrar qué columnas específicas están completas (las pocas)
            fila_ie = df_ie[df_ie['codigo_modular'] == codigo].iloc[0]
            cols_completas = fila_ie[fila_ie.notnull()].index.tolist()
            print(f"   Columnas COMPLETAS ({len(cols_completas)}): {', '.join(cols_completas)}")
    
    # Identificar IIEE con entre 50-80% NULL (problemáticas medias)
    medias_problematicas = df_analysis[
        (df_analysis['porcentaje_null'] > 50) & 
        (df_analysis['porcentaje_null'] <= 80)
    ]
    print(f"\n=== IIEE CON 50-80% VALORES NULL (PROBLEMÁTICAS MEDIAS): {len(medias_problematicas)} ===")
    
    if len(medias_problematicas) > 0:
        for idx, row in medias_problematicas.iterrows():
            print(f"Código: {row['codigo_modular']} | NULLs: {row['columnas_null']}/{total_cols} ({row['porcentaje_null']:.1f}%)")
    
    conn.close()
    return df_analysis

def analizar_indices_metodologicos():
    """Verificar estructura de tabla indices_metodologicos"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== ANÁLISIS TABLA INDICES_METODOLOGICOS ===")
    
    # Verificar estructura de la tabla
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(indices_metodologicos)")
    columnas = cursor.fetchall()
    
    print(f"Columnas en indices_metodologicos:")
    for col in columnas:
        print(f"  {col[1]} ({col[2]})")
    
    # Cargar datos
    df_indices = pd.read_sql_query("SELECT * FROM indices_metodologicos LIMIT 5", conn)
    print(f"\nPrimeras 5 filas de indices_metodologicos:")
    print(df_indices.to_string())
    
    conn.close()

def comparar_codigos_entre_tablas():
    """Comparar códigos modulares entre instituciones_educativas e indices_metodologicos"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== COMPARACIÓN CÓDIGOS ENTRE TABLAS ===")
    
    # Obtener códigos de instituciones_educativas
    df_ie_codigos = pd.read_sql_query("SELECT codigo_modular FROM instituciones_educativas", conn)
    codigos_ie = set(df_ie_codigos['codigo_modular'])
    
    # Verificar qué columna contiene códigos en indices_metodologicos
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(indices_metodologicos)")
    columnas_indices = [col[1] for col in cursor.fetchall()]
    
    print(f"Columnas disponibles en indices_metodologicos: {columnas_indices}")
    
    # Intentar encontrar la columna de códigos
    posibles_columnas_codigo = ['codigo_modular', 'cod_mod', 'codigo', 'id']
    columna_codigo_encontrada = None
    
    for col in posibles_columnas_codigo:
        if col in columnas_indices:
            columna_codigo_encontrada = col
            break
    
    if columna_codigo_encontrada:
        print(f"Columna de código encontrada: {columna_codigo_encontrada}")
        
        # Obtener códigos de indices_metodologicos
        df_indices_codigos = pd.read_sql_query(f"SELECT {columna_codigo_encontrada} FROM indices_metodologicos", conn)
        codigos_indices = set(df_indices_codigos[columna_codigo_encontrada])
        
        print(f"Códigos en instituciones_educativas: {len(codigos_ie)}")
        print(f"Códigos en indices_metodologicos: {len(codigos_indices)}")
        
        # Encontrar diferencias
        solo_en_ie = codigos_ie - codigos_indices
        solo_en_indices = codigos_indices - codigos_ie
        
        print(f"\nCódigos solo en instituciones_educativas: {len(solo_en_ie)}")
        if len(solo_en_ie) <= 10:
            print(f"  {sorted(solo_en_ie)}")
        else:
            print(f"  Primeros 10: {sorted(list(solo_en_ie))[:10]}")
        
        print(f"\nCódigos solo en indices_metodologicos: {len(solo_en_indices)}")
        if len(solo_en_indices) <= 10:
            print(f"  {sorted(solo_en_indices)}")
        else:
            print(f"  Primeros 10: {sorted(list(solo_en_indices))[:10]}")
    else:
        print("No se encontró columna de código en indices_metodologicos")
    
    conn.close()

def analizar_columnas_mas_null():
    """Análizar las columnas con más valores NULL"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("\n=== COLUMNAS CON MÁS VALORES NULL ===")
    
    df_ie = pd.read_sql_query("SELECT * FROM instituciones_educativas", conn)
    
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
    
    print("Top 20 columnas con más NULL:")
    for idx, row in col_analysis.head(20).iterrows():
        print(f"{row['columna']:40} | NULL: {row['valores_null']:3d} ({row['porcentaje_null']:5.1f}%) | Completos: {row['valores_completos']:3d}")
    
    conn.close()
    return col_analysis

def main():
    """Función principal"""
    
    print("ANÁLISIS ESPECÍFICO DE NULLS - REASIS DATABASE V4")
    print("=" * 70)
    
    try:
        # 1. Análisis de IIEE problemáticas específico
        df_problematicas = analizar_iiee_problematicas_especifico()
        
        # 2. Análisis de columnas con más NULL
        col_analysis = analizar_columnas_mas_null()
        
        # 3. Verificar estructura de indices_metodologicos
        analizar_indices_metodologicos()
        
        # 4. Comparar códigos entre tablas
        comparar_codigos_entre_tablas()
        
        print("\n" + "=" * 70)
        print("ANÁLISIS COMPLETADO")
        
    except Exception as e:
        print(f"Error en análisis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()