#!/usr/bin/env python3
"""
Script para revisar estructura de tabla indices_metodologicos
y identificar variables redundantes
"""

import sqlite3
import pandas as pd

def revisar_estructura_tabla():
    """
    Examina la estructura completa de la tabla indices_metodologicos
    """
    
    print("=== ESTRUCTURA TABLA INDICES_METODOLOGICOS ===\n")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # 1. Información de columnas
    cursor.execute('PRAGMA table_info(indices_metodologicos)')
    columns_info = cursor.fetchall()
    
    print(f"1. INFORMACIÓN DE COLUMNAS:")
    print(f"   Total columnas: {len(columns_info)}")
    print(f"\n   Estructura detallada:")
    print(f"   {'#':<3} {'Nombre':<30} {'Tipo':<12} {'PK':<3} {'NOT NULL':<9}")
    print(f"   {'-'*3} {'-'*30} {'-'*12} {'-'*3} {'-'*9}")
    
    for i, (cid, name, type_, notnull, default, pk) in enumerate(columns_info, 1):
        pk_mark = "PK" if pk else "  "
        null_mark = "NOT NULL" if notnull else "        "
        print(f"   {i:2d}. {name:<30} {type_:<12} {pk_mark:<3} {null_mark}")
    
    # 2. Identificar variables X13_TMATRC relacionadas
    print(f"\n2. VARIABLES X13_TMATRC IDENTIFICADAS:")
    
    x13_variables = []
    for _, name, _, _, _, _ in columns_info:
        if 'X13' in name or 'TMATRC' in name:
            x13_variables.append(name)
    
    print(f"   Variables encontradas: {len(x13_variables)}")
    for var in x13_variables:
        print(f"   - {var}")
    
    # 3. Analizar contenido de variables X13
    if x13_variables:
        print(f"\n3. ANÁLISIS DE CONTENIDO VARIABLES X13:")
        
        for var in x13_variables:
            try:
                # Estadísticas básicas
                query_stats = f"""
                SELECT 
                    COUNT(*) as total_registros,
                    COUNT({var}) as con_datos,
                    COUNT(*) - COUNT({var}) as null_count
                FROM indices_metodologicos
                """
                stats = cursor.execute(query_stats).fetchone()
                
                print(f"\n   {var}:")
                print(f"     Total registros: {stats[0]}")
                print(f"     Con datos: {stats[1]}")
                print(f"     NULL: {stats[2]}")
                
                if stats[1] > 0:  # Si hay datos
                    # Muestra de valores únicos
                    query_sample = f"""
                    SELECT DISTINCT {var}, COUNT(*) as frequency
                    FROM indices_metodologicos 
                    WHERE {var} IS NOT NULL
                    GROUP BY {var}
                    ORDER BY frequency DESC
                    LIMIT 10
                    """
                    sample = cursor.execute(query_sample).fetchall()
                    
                    print(f"     Valores únicos (top 10):")
                    for value, freq in sample:
                        print(f"       {value}: {freq} instituciones")
                        
            except Exception as e:
                print(f"     ERROR analizando {var}: {str(e)}")
    
    # 4. Buscar otras variables potencialmente redundantes
    print(f"\n4. BÚSQUEDA DE OTRAS VARIABLES REDUNDANTES:")
    
    # Variables con sufijos similares
    variable_groups = {}
    for _, name, _, _, _, _ in columns_info:
        # Buscar patrones base (antes del sufijo)
        base_name = name.split('_')[0] if '_' in name else name
        if base_name not in variable_groups:
            variable_groups[base_name] = []
        variable_groups[base_name].append(name)
    
    # Mostrar grupos con múltiples variables
    redundant_candidates = []
    for base, variables in variable_groups.items():
        if len(variables) > 1 and any('_' in var for var in variables):
            redundant_candidates.append((base, variables))
    
    if redundant_candidates:
        print(f"   Grupos de variables posiblemente redundantes:")
        for base, variables in redundant_candidates:
            print(f"     {base}: {', '.join(variables)}")
    else:
        print(f"   No se encontraron grupos obviamente redundantes")
    
    conn.close()
    
    return columns_info, x13_variables, redundant_candidates

if __name__ == "__main__":
    cols_info, x13_vars, redundant = revisar_estructura_tabla()
    
    print(f"\n=== RESUMEN ESTRUCTURA ===")
    print(f"Total columnas: {len(cols_info)}")
    print(f"Variables X13_TMATRC: {len(x13_vars)}")
    print(f"Grupos redundantes candidatos: {len(redundant)}")
    
    if x13_vars:
        print(f"\n[ACCIÓN REQUERIDA] Evaluar redundancia en variables X13:")
        for var in x13_vars:
            print(f"  - {var}")
    
    if redundant:
        print(f"\n[REVISIÓN SUGERIDA] Otros grupos para evaluar:")
        for base, variables in redundant:
            print(f"  - {base}: {len(variables)} variables")