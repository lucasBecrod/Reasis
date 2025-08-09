#!/usr/bin/env python3
"""
Analizar estado actual de columnas numero_fya y numero_fya_secundario
Proyecto Reasis - Normalización de códigos de red
"""

import sqlite3
import pandas as pd
import re

def main():
    print("=== ANÁLISIS DE COLUMNAS numero_fya ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # 1. Analizar valores únicos en numero_fya
    print("1. Valores únicos en numero_fya:")
    df_unicos = pd.read_sql_query("""
        SELECT DISTINCT numero_fya, COUNT(*) as cantidad
        FROM instituciones_educativas 
        WHERE numero_fya IS NOT NULL AND numero_fya != ''
        GROUP BY numero_fya
        ORDER BY cantidad DESC
    """, conn)
    
    print(f"Total formatos únicos: {len(df_unicos)}")
    print(df_unicos.to_string())
    
    # 2. Relación con nombre_red_fya_matched
    print("\n2. Relación numero_fya vs nombre_red_fya_matched:")
    df_relacion = pd.read_sql_query("""
        SELECT numero_fya, nombre_red_fya_matched, COUNT(*) as cantidad
        FROM instituciones_educativas 
        WHERE numero_fya IS NOT NULL AND numero_fya != ''
            AND nombre_red_fya_matched IS NOT NULL AND nombre_red_fya_matched != ''
        GROUP BY numero_fya, nombre_red_fya_matched
        ORDER BY cantidad DESC
        LIMIT 20
    """, conn)
    
    print(df_relacion.to_string())
    
    # 3. Analizar numero_fya_secundario
    print("\n3. Valores únicos en numero_fya_secundario:")
    df_secundario = pd.read_sql_query("""
        SELECT DISTINCT numero_fya_secundario, COUNT(*) as cantidad
        FROM instituciones_educativas 
        WHERE numero_fya_secundario IS NOT NULL AND numero_fya_secundario != ''
        GROUP BY numero_fya_secundario
        ORDER BY cantidad DESC
    """, conn)
    
    print(f"Total valores secundarios: {len(df_secundario)}")
    if len(df_secundario) > 0:
        print(df_secundario.to_string())
    else:
        print("No hay valores en numero_fya_secundario")
    
    # 4. Extraer códigos de red de nombre_red_fya_matched
    print("\n4. Extracción de códigos desde nombre_red_fya_matched:")
    df_todas = pd.read_sql_query("""
        SELECT codigo_modular, numero_fya, nombre_red_fya_matched
        FROM instituciones_educativas 
        WHERE nombre_red_fya_matched IS NOT NULL AND nombre_red_fya_matched != ''
        LIMIT 20
    """, conn)
    
    print("Muestra de datos para análisis:")
    for _, row in df_todas.iterrows():
        nombre_red = row['nombre_red_fya_matched']
        # Extraer número de la red usando regex
        match = re.search(r'Red Fe y Alegría (\d+)', nombre_red)
        codigo_extraido = match.group(1) if match else 'N/A'
        
        print(f"Código: {row['codigo_modular']} | numero_fya: {row['numero_fya']} | Red: {nombre_red} | Extraído: {codigo_extraido}")
    
    # 5. Estadísticas generales
    print("\n5. Estadísticas generales:")
    stats = pd.read_sql_query("""
        SELECT 
            COUNT(*) as total_registros,
            COUNT(CASE WHEN numero_fya IS NOT NULL AND numero_fya != '' THEN 1 END) as con_numero_fya,
            COUNT(CASE WHEN numero_fya_secundario IS NOT NULL AND numero_fya_secundario != '' THEN 1 END) as con_secundario,
            COUNT(CASE WHEN nombre_red_fya_matched IS NOT NULL AND nombre_red_fya_matched != '' THEN 1 END) as con_red_matched
        FROM instituciones_educativas
    """, conn)
    
    print(stats.to_string())
    
    conn.close()
    print("\n¡ANÁLISIS COMPLETADO!")

if __name__ == "__main__":
    main()