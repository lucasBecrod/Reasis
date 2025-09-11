#!/usr/bin/env python3
"""
Análisis exhaustivo de valores NULL en variables contextuales X14-X25
para desarrollo de metodología de imputación estadística profesional
"""

import sqlite3
import pandas as pd
import numpy as np
from scipy import stats
import seaborn as sns
import matplotlib.pyplot as plt

def analizar_nulls_variables_contextuales():
    """
    Analiza detalladamente los valores NULL en variables contextuales
    """
    
    print("=== ANALISIS EXHAUSTIVO VALORES NULL VARIABLES CONTEXTUALES ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Cargar datos completos
    query = """
    SELECT 
        CODIGO_MODULAR, NOMBRE_INSTITUCION, NUMERO_FYA, ALTITUD_MSNM,
        -- Variables metodológicas clave para contexto
        Y1_ILA, X1_NVC, X2_TR, X11_RED, X24_GPMD,
        -- Variables contextuales nuevas
        X14_NIVEL_EDUCATIVO, X16_MODALIDAD, X17_GESTION, X18_TURNO,
        X19_ORGANIZACION_PEDAGOGICA, X20_DIRECTIVOS_TOTAL,
        X21_MULTIPLICIDAD1, X22_MULTIPLICIDAD2, X25_POBLACION_DISTRITO
    FROM indices_metodologicos
    """
    
    df = pd.read_sql_query(query, conn)
    
    print("1. ESTADO GENERAL DE COMPLETITUD:")
    print(f"   Total instituciones: {len(df)}")
    
    # 2. Análisis de completitud por variable
    variables_contextuales = [
        'X14_NIVEL_EDUCATIVO', 'X16_MODALIDAD', 'X17_GESTION', 'X18_TURNO',
        'X19_ORGANIZACION_PEDAGOGICA', 'X20_DIRECTIVOS_TOTAL',
        'X21_MULTIPLICIDAD1', 'X22_MULTIPLICIDAD2', 'X24_GPMD', 'X25_POBLACION_DISTRITO'
    ]
    
    print(f"\n2. ANALISIS COMPLETITUD VARIABLES CONTEXTUALES:")
    
    completitud_data = []
    for var in variables_contextuales:
        total = len(df)
        no_nulls = df[var].notna().sum()
        nulls = total - no_nulls
        completitud = (no_nulls / total) * 100
        
        completitud_data.append({
            'variable': var,
            'total': total,
            'con_datos': no_nulls,
            'nulls': nulls,
            'completitud_pct': completitud
        })
        
        print(f"   {var}:")
        print(f"     Con datos: {no_nulls}/{total} ({completitud:.1f}%)")
        print(f"     NULLs: {nulls} ({100-completitud:.1f}%)")
        
        if nulls > 0:
            print(f"     [REQUIERE IMPUTACION]")
        else:
            print(f"     [COMPLETA]")
        print()
    
    # 3. Identificar instituciones con múltiples NULLs
    print("3. ANALISIS INSTITUCIONES CON MULTIPLES NULLs:")
    
    df_nulls = df[variables_contextuales].isnull()
    instituciones_nulls = df_nulls.sum(axis=1)
    
    print(f"   Distribución de NULLs por institución:")
    null_distribution = instituciones_nulls.value_counts().sort_index()
    
    for num_nulls, count in null_distribution.items():
        if num_nulls > 0:
            pct = (count / len(df)) * 100
            print(f"     {num_nulls} variables con NULL: {count} instituciones ({pct:.1f}%)")
    
    # Instituciones con más problemas
    instituciones_problematicas = df[instituciones_nulls >= 3]
    if len(instituciones_problematicas) > 0:
        print(f"\n   Instituciones con ≥3 NULLs (más problemáticas):")
        for _, inst in instituciones_problematicas.iterrows():
            nulls_vars = [var for var in variables_contextuales if pd.isna(inst[var])]
            print(f"     {inst['CODIGO_MODULAR']}: {inst['NOMBRE_INSTITUCION']}")
            print(f"       Variables NULL: {', '.join(nulls_vars)}")
            print(f"       Red: {inst['NUMERO_FYA']}, Ruralidad: {inst['X2_TR']}")
    
    # 4. Análisis de patrones de NULLs por contexto
    print(f"\n4. PATRONES DE NULLs POR CONTEXTO:")
    
    # Por red Fe y Alegría
    print(f"\n   Por Red Fe y Alegría:")
    for red in sorted(df['NUMERO_FYA'].dropna().unique()):
        df_red = df[df['NUMERO_FYA'] == red]
        null_rate_red = (df_red[variables_contextuales].isnull().sum().sum()) / (len(df_red) * len(variables_contextuales)) * 100
        print(f"     Red {red}: {len(df_red)} inst, {null_rate_red:.1f}% NULLs promedio")
    
    # Por ruralidad
    print(f"\n   Por Ruralidad:")
    for ruralidad in [1, 2]:  # 1=Urbano, 2=Rural
        tipo = "Urbano" if ruralidad == 1 else "Rural"
        df_rural = df[df['X2_TR'] == ruralidad]
        if len(df_rural) > 0:
            null_rate_rural = (df_rural[variables_contextuales].isnull().sum().sum()) / (len(df_rural) * len(variables_contextuales)) * 100
            print(f"     {tipo}: {len(df_rural)} inst, {null_rate_rural:.1f}% NULLs promedio")
    
    # 5. Análisis de correlaciones entre variables para imputación
    print(f"\n5. CORRELACIONES PARA ESTRATEGIAS DE IMPUTACION:")
    
    # Variables numéricas para correlación
    vars_numericas = ['ALTITUD_MSNM', 'Y1_ILA', 'X1_NVC', 'X11_RED', 'X24_GPMD', 'X25_POBLACION_DISTRITO',
                     'X20_DIRECTIVOS_TOTAL', 'X21_MULTIPLICIDAD1', 'X22_MULTIPLICIDAD2']
    
    df_corr = df[vars_numericas].corr()
    
    print(f"   Correlaciones relevantes (>0.3) para imputación:")
    correlaciones_fuertes = []
    
    for i, var1 in enumerate(vars_numericas):
        for var2 in vars_numericas[i+1:]:
            corr = df_corr.loc[var1, var2]
            if abs(corr) > 0.3 and not pd.isna(corr):
                correlaciones_fuertes.append((var1, var2, corr))
                print(f"     {var1} <-> {var2}: r={corr:.3f}")
    
    # 6. Análisis de distribuciones por categorías clave
    print(f"\n6. DISTRIBUCIONES POR CATEGORIAS PARA IMPUTACION MODAL:")
    
    variables_categoricas = ['X14_NIVEL_EDUCATIVO', 'X16_MODALIDAD', 'X17_GESTION', 
                            'X18_TURNO', 'X19_ORGANIZACION_PEDAGOGICA']
    
    for var_cat in variables_categoricas:
        if df[var_cat].notna().sum() > 0:
            print(f"\n   {var_cat}:")
            
            # Por ruralidad
            for ruralidad in [1, 2]:
                tipo_rural = "Urbano" if ruralidad == 1 else "Rural"
                df_subset = df[df['X2_TR'] == ruralidad]
                if len(df_subset) > 0:
                    moda = df_subset[var_cat].mode()
                    if len(moda) > 0:
                        valor_modal = moda[0]
                        freq = df_subset[var_cat].value_counts().iloc[0] if not df_subset[var_cat].dropna().empty else 0
                        total_validos = df_subset[var_cat].notna().sum()
                        pct_modal = (freq / total_validos * 100) if total_validos > 0 else 0
                        print(f"     {tipo_rural}: Moda={valor_modal}, Freq={freq}/{total_validos} ({pct_modal:.1f}%)")
    
    # 7. Identificar variables predictoras disponibles
    print(f"\n7. VARIABLES PREDICTORAS DISPONIBLES:")
    
    variables_predictoras = {
        'geograficas': ['ALTITUD_MSNM', 'X2_TR'],
        'institucionales': ['NUMERO_FYA', 'Y1_ILA', 'X11_RED'],
        'contextuales': ['X1_NVC', 'X24_GPMD', 'X25_POBLACION_DISTRITO']
    }
    
    for categoria, vars_pred in variables_predictoras.items():
        print(f"   {categoria.title()}:")
        for var in vars_pred:
            if var in df.columns:
                completitud_pred = (df[var].notna().sum() / len(df)) * 100
                print(f"     {var}: {completitud_pred:.1f}% completitud")
    
    conn.close()
    
    return df, completitud_data, correlaciones_fuertes

def proponer_estrategias_imputacion(df, completitud_data, correlaciones):
    """
    Propone estrategias específicas de imputación por variable
    """
    
    print(f"\n8. ESTRATEGIAS DE IMPUTACION PROPUESTAS:")
    
    estrategias = {}
    
    # Variables con NULLs que necesitan imputación
    vars_con_nulls = [item for item in completitud_data if item['nulls'] > 0]
    
    for var_info in vars_con_nulls:
        var_name = var_info['variable']
        nulls_count = var_info['nulls']
        completitud = var_info['completitud_pct']
        
        print(f"\n   {var_name} ({nulls_count} NULLs, {completitud:.1f}% completitud):")
        
        if var_name == 'X17_GESTION':
            estrategia = {
                'metodo': 'MODAL_CONTEXTUAL',
                'descripcion': 'Imputación por moda según ruralidad y red',
                'predictores': ['X2_TR', 'NUMERO_FYA'],
                'fallback': 'Moda global',
                'justificacion': 'Gestión depende del contexto territorial y red específica'
            }
            
        elif var_name in ['X19_ORGANIZACION_PEDAGOGICA']:
            estrategia = {
                'metodo': 'REGRESION_ORDINAL',
                'descripcion': 'Regresión ordinal usando tamaño institucional y ruralidad',
                'predictores': ['X11_RED', 'X2_TR', 'X25_POBLACION_DISTRITO'],
                'fallback': 'Moda por estrato rural/urbano',
                'justificacion': 'Organización pedagógica correlaciona con tamaño y contexto'
            }
            
        elif var_name in ['X20_DIRECTIVOS_TOTAL']:
            estrategia = {
                'metodo': 'REGRESION_POISSON',
                'descripcion': 'Regresión Poisson para variable de conteo',
                'predictores': ['X11_RED', 'Y1_ILA', 'X25_POBLACION_DISTRITO'],
                'fallback': 'Media por estrato de tamaño',
                'justificacion': 'Número directivos depende del tamaño institucional'
            }
            
        elif var_name in ['X21_MULTIPLICIDAD1', 'X22_MULTIPLICIDAD2']:
            estrategia = {
                'metodo': 'K_NEAREST_NEIGHBORS',
                'descripcion': 'KNN con variables institucionales similares',
                'predictores': ['X2_TR', 'X11_RED', 'ALTITUD_MSNM', 'NUMERO_FYA'],
                'fallback': 'Valor modal por red',
                'justificacion': 'Multiplicidad refleja características institucionales complejas'
            }
            
        else:
            # Estrategia genérica para otras variables
            estrategia = {
                'metodo': 'MODAL_ESTRATIFICADO',
                'descripcion': 'Moda por estratos contextuales',
                'predictores': ['X2_TR', 'NUMERO_FYA'],
                'fallback': 'Moda global',
                'justificacion': 'Variables categóricas con patrones por contexto'
            }
        
        estrategias[var_name] = estrategia
        
        print(f"     Método: {estrategia['metodo']}")
        print(f"     Descripción: {estrategia['descripcion']}")
        print(f"     Predictores: {', '.join(estrategia['predictores'])}")
        print(f"     Fallback: {estrategia['fallback']}")
        print(f"     Justificación: {estrategia['justificacion']}")
    
    return estrategias

if __name__ == "__main__":
    print("Iniciando análisis exhaustivo de NULLs en variables contextuales...")
    
    # Ejecutar análisis
    df_data, completitud_info, correlaciones_fuertes = analizar_nulls_variables_contextuales()
    
    # Proponer estrategias
    estrategias_imputacion = proponer_estrategias_imputacion(df_data, completitud_info, correlaciones_fuertes)
    
    print(f"\n=== RESUMEN ANALISIS ===")
    print(f"Variables contextuales analizadas: 10")
    print(f"Variables que requieren imputación: {len([item for item in completitud_info if item['nulls'] > 0])}")
    print(f"Correlaciones fuertes identificadas: {len(correlaciones_fuertes)}")
    print(f"Estrategias de imputación diseñadas: {len(estrategias_imputacion)}")
    
    print(f"\n[SIGUIENTE PASO] Implementar metodología estadística profesional de imputación")