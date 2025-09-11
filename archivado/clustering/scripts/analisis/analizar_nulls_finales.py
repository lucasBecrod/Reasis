#!/usr/bin/env python3
"""
Script para identificar instituciones con valores NULL en variables metodológicas
y analizar estrategias de imputación final
"""

import sqlite3
import pandas as pd
import numpy as np

def analizar_nulls_finales():
    """
    Analiza valores NULL restantes en todas las variables metodológicas
    """
    
    print("=== ANÁLISIS DE VALORES NULL FINALES ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Identificar instituciones con X10_IE NULL
    print("1. INSTITUCIONES CON X10_IE NULL:")
    
    df_x10_null = pd.read_sql_query("""
        SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION, NUMERO_FYA, X2_TR, X10_IE 
        FROM indices_metodologicos 
        WHERE X10_IE IS NULL
    """, conn)
    
    print(f"   Total instituciones con X10_IE NULL: {len(df_x10_null)}")
    
    if len(df_x10_null) > 0:
        print(f"\n   Detalle instituciones:")
        for _, row in df_x10_null.iterrows():
            red = row['NUMERO_FYA'] if pd.notna(row['NUMERO_FYA']) else 'Sin Red'
            ruralidad = row['X2_TR'] if pd.notna(row['X2_TR']) else 'Sin Dato'
            print(f"   - {row['CODIGO_MODULAR']}: {row['NOMBRE_INSTITUCION']}")
            print(f"     Red: {red}, Ruralidad: {ruralidad}")
    
    # 2. Análisis completo de NULL por variable
    print(f"\n2. ANÁLISIS COMPLETO DE NULL POR VARIABLE:")
    
    variables_metodologicas = [
        'Y1_ILA', 'Y2_TD', 'Y3_PR', 
        'X1_NVC', 'X2_TR', 'X4_IDD', 'X5_ED', 'X6_CDD', 
        'X10_IE', 'X11_RED', 'X12_TOE', 'X15_MEIB'
    ]
    
    null_analysis = []
    
    for variable in variables_metodologicas:
        query = f"""
        SELECT 
            COUNT(*) as total_registros,
            COUNT({variable}) as con_datos,
            COUNT(*) - COUNT({variable}) as null_count,
            (COUNT(*) - COUNT({variable})) * 100.0 / COUNT(*) as null_percentage
        FROM indices_metodologicos
        """
        
        result = pd.read_sql_query(query, conn).iloc[0]
        
        null_analysis.append({
            'variable': variable,
            'total': result['total_registros'],
            'con_datos': result['con_datos'],
            'null_count': result['null_count'],
            'null_percentage': result['null_percentage']
        })
    
    df_null_analysis = pd.DataFrame(null_analysis)
    
    print(f"\n   Resumen NULL por variable:")
    print(f"   {'Variable':<8} {'Total':<6} {'Datos':<6} {'NULL':<5} {'%NULL':<6}")
    print(f"   {'-'*8} {'-'*6} {'-'*6} {'-'*5} {'-'*6}")
    
    for _, row in df_null_analysis.iterrows():
        status = "OK" if row['null_count'] == 0 else "ERROR" if row['null_count'] > 5 else "WARN"
        print(f"   {row['variable']:<8} {row['total']:<6} {row['con_datos']:<6} {row['null_count']:<5} {row['null_percentage']:<6.1f} {status}")
    
    # 3. Variables con NULL restantes
    variables_con_null = df_null_analysis[df_null_analysis['null_count'] > 0]
    
    print(f"\n3. VARIABLES CON NULL RESTANTES:")
    print(f"   Total variables con NULL: {len(variables_con_null)}")
    
    if len(variables_con_null) > 0:
        print(f"\n   Variables problemáticas:")
        for _, row in variables_con_null.iterrows():
            print(f"   - {row['variable']}: {row['null_count']} NULL ({row['null_percentage']:.1f}%)")
    
    # 4. Análisis detallado de instituciones con múltiples NULL
    print(f"\n4. INSTITUCIONES CON MÚLTIPLES NULL:")
    
    if len(variables_con_null) > 0:
        variables_null = variables_con_null['variable'].tolist()
        null_columns = []
        
        for var in variables_null:
            null_columns.append(f"CASE WHEN {var} IS NULL THEN 1 ELSE 0 END")
        
        query_multiples_null = f"""
        SELECT 
            CODIGO_MODULAR, 
            NOMBRE_INSTITUCION, 
            NUMERO_FYA, 
            X2_TR,
            {' + '.join(null_columns)} as total_nulls,
            {', '.join(variables_null)}
        FROM indices_metodologicos 
        WHERE ({' + '.join(null_columns)}) > 0
        ORDER BY total_nulls DESC, CODIGO_MODULAR
        """
        
        df_multiples_null = pd.read_sql_query(query_multiples_null, conn)
        
        print(f"   Instituciones con NULL en al menos 1 variable: {len(df_multiples_null)}")
        
        if len(df_multiples_null) > 0:
            print(f"\n   TOP instituciones con más NULL:")
            for _, row in df_multiples_null.head(10).iterrows():
                nulls_detalle = []
                for var in variables_null:
                    if pd.isna(row[var]):
                        nulls_detalle.append(var)
                
                red = row['NUMERO_FYA'] if pd.notna(row['NUMERO_FYA']) else 'Sin Red'
                print(f"   - {row['CODIGO_MODULAR']}: {row['total_nulls']} NULLs")
                print(f"     Nombre: {row['NOMBRE_INSTITUCION'][:50]}...")
                print(f"     Red: {red}, Variables NULL: {', '.join(nulls_detalle)}")
    
    # 5. Estrategias de imputación por variable
    print(f"\n5. ESTRATEGIAS DE IMPUTACIÓN RECOMENDADAS:")
    
    estrategias_imputacion = {
        'Y1_ILA': 'Promedio por red y nivel educativo',
        'Y2_TD': 'Valor 0 (sin tendencia) o promedio contextual',
        'Y3_PR': 'Mediana por estrato (red + ruralidad)',
        'X1_NVC': 'Valor 4 (alta vulnerabilidad Fe y Alegría)',
        'X2_TR': 'Inferencia por ubicación geográfica',
        'X4_IDD': 'Promedio por red o valor medio 2.5',
        'X5_ED': 'Promedio por tipo de zona (rural/urbana)',
        'X6_CDD': 'Promedio por red educativa',
        'X10_IE': 'Promedio por ruralidad (urbana/rural)',
        'X11_RED': 'Ratio calculado desde matrícula/docentes',
        'X12_TOE': 'Inferencia por número de docentes',
        'X15_MEIB': 'Valor 0 (No EIB) por defecto'
    }
    
    for _, row in variables_con_null.iterrows():
        var = row['variable']
        estrategia = estrategias_imputacion.get(var, 'Promedio general')
        
        print(f"   {var} ({row['null_count']} NULL): {estrategia}")
    
    # 6. Calcular contexto para imputación X10_IE
    if len(df_x10_null) > 0:
        print(f"\n6. CONTEXTO PARA IMPUTACIÓN X10_IE:")
        
        # Promedio por ruralidad
        promedios_ruralidad = pd.read_sql_query("""
            SELECT 
                X2_TR,
                COUNT(*) as instituciones,
                AVG(X10_IE) as promedio_x10ie,
                CASE X2_TR 
                    WHEN 1 THEN 'Urbano'
                    WHEN 2 THEN 'Rural'
                    ELSE 'Otro'
                END as tipo_ruralidad
            FROM indices_metodologicos 
            WHERE X10_IE IS NOT NULL AND X2_TR IS NOT NULL
            GROUP BY X2_TR
        """, conn)
        
        print(f"   Promedios X10_IE por ruralidad:")
        for _, row in promedios_ruralidad.iterrows():
            print(f"   - {row['tipo_ruralidad']} (X2_TR={row['X2_TR']}): {row['promedio_x10ie']:.4f}")
        
        # Análisis de instituciones NULL
        print(f"\n   Instituciones NULL por contexto:")
        contexto_null = df_x10_null.groupby(['X2_TR']).size().reset_index(name='count')
        for _, row in contexto_null.iterrows():
            tipo = "Urbano" if row['X2_TR'] == 1 else "Rural" if row['X2_TR'] == 2 else "Otro"
            print(f"   - {tipo}: {row['count']} instituciones")
    
    conn.close()
    
    return df_null_analysis, len(df_x10_null)

if __name__ == "__main__":
    df_analysis, x10_nulls = analizar_nulls_finales()
    
    total_nulls = df_analysis['null_count'].sum()
    variables_con_nulls = (df_analysis['null_count'] > 0).sum()
    
    print(f"\n=== RESUMEN FINAL ===")
    print(f"Total NULL en todas las variables: {total_nulls}")
    print(f"Variables con NULL: {variables_con_nulls}/12")
    print(f"X10_IE NULL específicamente: {x10_nulls}")
    
    if total_nulls == 0:
        print(f"\n[PERFECTO] Base de datos 100% completa sin NULL")
    elif total_nulls <= 10:
        print(f"\n[EXCELENTE] Muy pocos NULL, fácil imputación")
    elif total_nulls <= 50:
        print(f"\n[BUENO] NULL manejables con imputación")
    else:
        print(f"\n[ATENCION] Muchos NULL, revisar estrategia")