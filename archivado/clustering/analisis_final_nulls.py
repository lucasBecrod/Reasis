#!/usr/bin/env python3
"""
Análisis final de valores NULL - Reporte completo para el usuario
"""

import sqlite3
import pandas as pd
import numpy as np

def generar_reporte_completo():
    """Generar reporte completo de análisis de NULL"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("=" * 80)
    print("REPORTE FINAL: ANÁLISIS DE VALORES NULL EN BASE DE DATOS REASIS V4")
    print("=" * 80)
    
    # 1. INFORMACIÓN GENERAL
    df_ie = pd.read_sql_query("SELECT * FROM instituciones_educativas", conn)
    print(f"\n1. INFORMACIÓN GENERAL:")
    print(f"   - Total instituciones: {len(df_ie)}")
    print(f"   - Total columnas: {len(df_ie.columns)}")
    
    # 2. IIEE CON MÁS VALORES NULL
    null_counts = df_ie.isnull().sum(axis=1)
    total_cols = len(df_ie.columns)
    null_percentage = (null_counts / total_cols) * 100
    
    print(f"\n2. IIEE CON MÁS VALORES NULL:")
    print(f"   - Promedio de columnas NULL por IIEE: {null_counts.mean():.1f}")
    print(f"   - Promedio porcentaje NULL: {null_percentage.mean():.1f}%")
    
    # Identificar las más problemáticas
    muy_problematicas = df_ie[null_percentage > 80]
    problematicas_medias = df_ie[(null_percentage > 15) & (null_percentage <= 80)]
    
    print(f"   - IIEE con >80% NULL (MUY PROBLEMÁTICAS): {len(muy_problematicas)}")
    print(f"   - IIEE con 15-80% NULL (PROBLEMÁTICAS MEDIAS): {len(problematicas_medias)}")
    
    # 3. CÓDIGOS MODULARES DE IIEE PROBLEMÁTICAS
    print(f"\n3. CÓDIGOS MODULARES DE IIEE MUY PROBLEMÁTICAS (>80% NULL):")
    
    if len(muy_problematicas) > 0:
        for idx in muy_problematicas.index:
            codigo = df_ie.loc[idx, 'codigo_modular']
            nombre = df_ie.loc[idx, 'nombre_institucion']
            numero_fya = df_ie.loc[idx, 'numero_fya']
            clustering = df_ie.loc[idx, 'entra_estudio_clustering']
            nulls = null_counts.iloc[idx]
            pct_null = null_percentage.iloc[idx]
            
            print(f"   CÓDIGO: {codigo}")
            print(f"     - NULLs: {nulls}/{total_cols} ({pct_null:.1f}%)")
            print(f"     - Nombre: {nombre if pd.notna(nombre) else 'SIN NOMBRE'}")
            print(f"     - Número FyA: {numero_fya if pd.notna(numero_fya) else 'NO DEFINIDO'}")
            print(f"     - En clustering: {clustering if pd.notna(clustering) else 'NO DEFINIDO'}")
            
            # Mostrar columnas completas (las pocas que tiene)
            fila = df_ie.loc[idx]
            cols_completas = fila[fila.notnull()].index.tolist()
            print(f"     - Columnas completas ({len(cols_completas)}): {', '.join(cols_completas[:8])}...")
            print()
    
    # 4. CÓDIGOS MODULARES DE IIEE PROBLEMÁTICAS MEDIAS
    print(f"4. CÓDIGOS MODULARES DE IIEE PROBLEMÁTICAS MEDIAS (15-80% NULL):")
    
    if len(problematicas_medias) > 0:
        for idx in problematicas_medias.index:
            codigo = df_ie.loc[idx, 'codigo_modular']
            nombre = df_ie.loc[idx, 'nombre_institucion']
            clustering = df_ie.loc[idx, 'entra_estudio_clustering']
            nulls = null_counts.iloc[idx]
            pct_null = null_percentage.iloc[idx]
            
            print(f"   CÓDIGO: {codigo} | NULLs: {nulls}/{total_cols} ({pct_null:.1f}%) | Clustering: {clustering}")
    
    # 5. COLUMNAS MÁS AFECTADAS
    print(f"\n5. COLUMNAS MÁS AFECTADAS POR VALORES NULL:")
    
    null_by_column = df_ie.isnull().sum()
    null_percentage_col = (null_by_column / len(df_ie)) * 100
    
    cols_problematicas = null_by_column[null_by_column > 0].sort_values(ascending=False)
    
    print(f"   Top 15 columnas con más valores NULL:")
    for col in cols_problematicas.head(15).index:
        nulls = null_by_column[col]
        pct = null_percentage_col[col]
        completos = len(df_ie) - nulls
        print(f"     {col:35} | NULL: {nulls:3d} ({pct:5.1f}%) | Completos: {completos:3d}")
    
    # 6. COMPARACIÓN CON INDICES_METODOLOGICOS
    print(f"\n6. COMPARACIÓN CON TABLA INDICES_METODOLOGICOS:")
    
    df_indices = pd.read_sql_query("SELECT CODIGO_MODULAR FROM indices_metodologicos", conn)
    
    codigos_ie = set(df_ie['codigo_modular'])
    codigos_indices = set(df_indices['CODIGO_MODULAR'])
    
    solo_en_ie = codigos_ie - codigos_indices
    solo_en_indices = codigos_indices - codigos_ie
    
    print(f"   - Códigos en instituciones_educativas: {len(codigos_ie)}")
    print(f"   - Códigos en indices_metodologicos: {len(codigos_indices)}")
    print(f"   - Códigos solo en instituciones_educativas: {len(solo_en_ie)}")
    print(f"   - Códigos solo en indices_metodologicos: {len(solo_en_indices)}")
    
    # 7. VERIFICAR SI PROBLEMÁTICAS ESTÁN EN INDICES
    print(f"\n7. VERIFICACIÓN: ¿LAS IIEE PROBLEMÁTICAS ESTÁN EN INDICES_METODOLOGICOS?")
    
    codigos_muy_problematicas = [df_ie.loc[idx, 'codigo_modular'] for idx in muy_problematicas.index]
    codigos_medias_problematicas = [df_ie.loc[idx, 'codigo_modular'] for idx in problematicas_medias.index]
    
    print(f"   IIEE MUY PROBLEMÁTICAS:")
    for codigo in codigos_muy_problematicas:
        en_indices = codigo in codigos_indices
        print(f"     {codigo}: {'SÍ está en indices_metodologicos' if en_indices else 'NO está en indices_metodologicos'}")
    
    if codigos_medias_problematicas:
        print(f"\n   IIEE PROBLEMÁTICAS MEDIAS:")
        for codigo in codigos_medias_problematicas:
            en_indices = codigo in codigos_indices
            print(f"     {codigo}: {'SÍ está en indices_metodologicos' if en_indices else 'NO está en indices_metodologicos'}")
    
    # 8. ESTADÍSTICAS DE COMPLETITUD POR IIEE PROBLEMÁTICA
    print(f"\n8. ESTADÍSTICAS DETALLADAS DE COMPLETITUD:")
    
    df_completitud = pd.DataFrame({
        'codigo_modular': df_ie['codigo_modular'],
        'nombre_institucion': df_ie['nombre_institucion'],
        'columnas_completas': total_cols - null_counts,
        'columnas_null': null_counts,
        'porcentaje_completo': 100 - null_percentage,
        'porcentaje_null': null_percentage,
        'en_clustering': df_ie['entra_estudio_clustering']
    }).sort_values('porcentaje_null', ascending=False)
    
    print(f"   Top 10 IIEE con mayor porcentaje de valores NULL:")
    for idx, row in df_completitud.head(10).iterrows():
        print(f"     {row['codigo_modular']} | Completas: {row['porcentaje_completo']:.1f}% | NULL: {row['porcentaje_null']:.1f}% | Clustering: {row['en_clustering']}")
    
    conn.close()
    
    return {
        'muy_problematicas': codigos_muy_problematicas,
        'medias_problematicas': codigos_medias_problematicas,
        'completitud': df_completitud,
        'columnas_problematicas': cols_problematicas.head(15).index.tolist()
    }

def main():
    """Función principal"""
    
    try:
        resultados = generar_reporte_completo()
        
        print("\n" + "=" * 80)
        print("RESUMEN EJECUTIVO:")
        print("=" * 80)
        
        print(f"✓ IIEE MUY PROBLEMÁTICAS (>80% NULL): {len(resultados['muy_problematicas'])} instituciones")
        print(f"  Códigos: {resultados['muy_problematicas']}")
        
        print(f"✓ IIEE PROBLEMÁTICAS MEDIAS (15-80% NULL): {len(resultados['medias_problematicas'])} instituciones")
        
        print(f"✓ COLUMNAS MÁS AFECTADAS: {len(resultados['columnas_problematicas'])} columnas con valores NULL")
        print(f"  Top 5: {resultados['columnas_problematicas'][:5]}")
        
        print(f"\n✓ RECOMENDACIÓN: Priorizar completar datos para códigos muy problemáticos")
        print(f"  que están marcados para entrar en clustering.")
        
    except Exception as e:
        print(f"Error en análisis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()