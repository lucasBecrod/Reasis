#!/usr/bin/env python3
"""
Script para verificar la integración final de variables contextuales
y revisar posibles problemas de codificación
"""

import sqlite3
import pandas as pd

def verificar_integracion_final():
    """
    Verifica la integración y revisa problemas de codificación
    """
    
    print("=== VERIFICACION INTEGRACION FINAL ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Estructura final de la tabla
    print("1. ESTRUCTURA FINAL DE LA TABLA:")
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(indices_metodologicos)')
    columns_info = cursor.fetchall()
    
    print(f"   Total columnas: {len(columns_info)}")
    print(f"   Columnas agregadas en esta sesión (X14-X23):")
    
    nuevas_variables = []
    for col_info in columns_info:
        col_name = col_info[1]
        if col_name.startswith('X1') and any(x in col_name for x in ['X14', 'X16', 'X17', 'X18', 'X19']) or col_name.startswith('X2'):
            nuevas_variables.append(col_name)
    
    for var in sorted(nuevas_variables):
        print(f"     - {var}")
    
    # 2. Revisar problemas de codificación específicos
    print(f"\n2. REVISION PROBLEMAS DE CODIFICACION:")
    
    # Cargar datos para análisis
    df = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
    df_instituciones = pd.read_sql_query("SELECT codigo_modular, nivel_educativo, gestion, codigo_carrera FROM instituciones_educativas", conn)
    
    # Problema 1: X14_NIVEL_EDUCATIVO con valores NULL
    print(f"\n   X14_NIVEL_EDUCATIVO - Valores no codificados:")
    df_merged = df.merge(df_instituciones, left_on='CODIGO_MODULAR', right_on='codigo_modular', how='left')
    problemas_nivel = df_merged[df_merged['X14_NIVEL_EDUCATIVO'].isna()]
    if len(problemas_nivel) > 0:
        print(f"     Instituciones con problema: {len(problemas_nivel)}")
        for _, row in problemas_nivel.iterrows():
            print(f"       {row['CODIGO_MODULAR']}: '{row['nivel_educativo']}'")
    else:
        print(f"     [OK] Sin problemas de codificación")
    
    # Problema 2: X17_GESTION con valores NULL  
    print(f"\n   X17_GESTION - Valores no codificados:")
    problemas_gestion = df_merged[df_merged['X17_GESTION'].isna()]
    if len(problemas_gestion) > 0:
        print(f"     Instituciones con problema: {len(problemas_gestion)}")
        valores_unicos = problemas_gestion['gestion'].value_counts()
        print(f"     Valores no reconocidos:")
        for valor, count in valores_unicos.items():
            print(f"       '{valor}': {count} instituciones")
    else:
        print(f"     [OK] Sin problemas de codificación")
    
    # 3. Estadísticas generales de las nuevas variables
    print(f"\n3. ESTADISTICAS NUEVAS VARIABLES:")
    
    variables_estadisticas = {
        'X14_NIVEL_EDUCATIVO': 'Nivel Educativo',
        'X16_MODALIDAD': 'Modalidad (1=No escol, 2=Escol)',
        'X17_GESTION': 'Gestión (1=Pública directa, 2=Pública privada, 3=Privada)',
        'X18_TURNO': 'Turno (1=Mañana, 2=Tarde, 3=Noche, 4-7=Combos)',
        'X19_ORGANIZACION_PEDAGOGICA': 'Organización (0=No aplica, 1=Unidoc, 2=Polidoc multi, 3=Polidoc completo)',
        'X20_DIRECTIVOS_TOTAL': 'Total Directivos',
        'X21_MULTIPLICIDAD1': 'Multiplicidad 1',
        'X22_MULTIPLICIDAD2': 'Multiplicidad 2',
        'X23_POBREZA_DISTRITO': 'Grupo Pobreza Distrito'
    }
    
    for var_code, descripcion in variables_estadisticas.items():
        if var_code in df.columns:
            serie = df[var_code]
            total = len(serie)
            no_nulls = serie.notna().sum()
            nulls = total - no_nulls
            completitud = (no_nulls / total) * 100
            
            print(f"\n   {var_code} - {descripcion}:")
            print(f"     Completitud: {no_nulls}/{total} ({completitud:.1f}%)")
            
            if no_nulls > 0:
                print(f"     Rango: {serie.min():.0f} - {serie.max():.0f}")
                print(f"     Media: {serie.mean():.2f}")
                
                # Distribución de valores
                valores = serie.value_counts().head(5)
                print(f"     Top 5 valores:")
                for valor, count in valores.items():
                    print(f"       {valor}: {count} instituciones ({count/no_nulls*100:.1f}%)")
    
    # 4. Verificar que ALTITUD ya esté presente
    print(f"\n4. VERIFICACION ALTITUD_MSNM:")
    if 'ALTITUD_MSNM' in df.columns:
        altitud_stats = df['ALTITUD_MSNM'].describe()
        print(f"   [OK] ALTITUD_MSNM ya presente en la tabla")
        print(f"   Estadísticas: Min={altitud_stats['min']:.0f}, Max={altitud_stats['max']:.0f}, Media={altitud_stats['mean']:.0f}")
        completitud_altitud = (df['ALTITUD_MSNM'].notna().sum() / len(df)) * 100
        print(f"   Completitud: {completitud_altitud:.1f}%")
    else:
        print(f"   [FALTA] ALTITUD_MSNM no encontrada - podría estar con otro nombre")
        # Buscar variantes
        cols_altitud = [col for col in df.columns if 'ALTITUD' in col.upper()]
        if cols_altitud:
            print(f"   Columnas relacionadas encontradas: {cols_altitud}")
        else:
            print(f"   No se encontraron columnas relacionadas con altitud")
    
    # 5. Resumen final para clustering
    print(f"\n5. RESUMEN PARA CLUSTERING K-MEANS:")
    
    # Variables metodológicas originales (Y1-Y3, X1-X15)
    variables_metodologicas = [col for col in df.columns if col.startswith(('Y1', 'Y2', 'Y3', 'X1', 'X2', 'X4', 'X5', 'X6', 'X10', 'X11', 'X12', 'X13', 'X15'))]
    variables_contextuales = [col for col in df.columns if col.startswith(('X14', 'X16', 'X17', 'X18', 'X19', 'X20', 'X21', 'X22', 'X23'))]
    variables_altitud = [col for col in df.columns if 'ALTITUD' in col.upper()]
    
    print(f"   Variables metodológicas originales: {len(variables_metodologicas)}")
    print(f"   Variables contextuales nuevas: {len(variables_contextuales)}")
    print(f"   Variables altitud: {len(variables_altitud)}")
    print(f"   TOTAL variables para clustering: {len(variables_metodologicas) + len(variables_contextuales) + len(variables_altitud)}")
    
    # Completitud promedio
    completitudes = []
    for var in variables_metodologicas + variables_contextuales + variables_altitud:
        if var in df.columns:
            completitud = (df[var].notna().sum() / len(df)) * 100
            completitudes.append(completitud)
    
    if completitudes:
        completitud_promedio = sum(completitudes) / len(completitudes)
        print(f"   Completitud promedio: {completitud_promedio:.1f}%")
    
    conn.close()
    
    return len(variables_metodologicas), len(variables_contextuales), len(variables_altitud)

if __name__ == "__main__":
    metodologicas, contextuales, altitud = verificar_integracion_final()
    
    total_variables = metodologicas + contextuales + altitud
    
    print(f"\n=== RESUMEN INTEGRACION EXITOSA ===")
    print(f"Variables metodológicas: {metodologicas}")
    print(f"Variables contextuales: {contextuales}")  
    print(f"Variables altitud: {altitud}")
    print(f"TOTAL VARIABLES: {total_variables}")
    print(f"\n[LISTO] Base optimizada para clustering K-Means robusto")