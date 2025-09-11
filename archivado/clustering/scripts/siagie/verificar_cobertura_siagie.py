#!/usr/bin/env python3
"""
Script para verificar la cobertura real de la búsqueda SIAGIE
"""

import sqlite3
import pandas as pd

def verificar_cobertura():
    print("=== VERIFICACIÓN COBERTURA SIAGIE ===\n")
    
    # 1. Total instituciones en BD
    conn = sqlite3.connect('reasis_database.db')
    
    cursor = conn.execute("SELECT COUNT(*) FROM instituciones_educativas")
    total_ie = cursor.fetchone()[0]
    
    cursor = conn.execute("""
        SELECT COUNT(*) FROM instituciones_educativas 
        WHERE codigo_modular IS NOT NULL AND codigo_modular != ''
    """)
    con_codigo = cursor.fetchone()[0]
    
    print(f"Total instituciones en BD: {total_ie}")
    print(f"Con código modular válido: {con_codigo}")
    print(f"Sin código modular: {total_ie - con_codigo}")
    
    # 2. Obtener todos los códigos disponibles (no solo 50)
    cursor = conn.execute("""
        SELECT codigo_modular, nombre_institucion, numero_fya
        FROM instituciones_educativas 
        WHERE codigo_modular IS NOT NULL AND codigo_modular != ''
        ORDER BY numero_fya
    """)
    
    todas_instituciones = []
    for row in cursor.fetchall():
        todas_instituciones.append({
            'codigo_modular': row[0],
            'nombre': row[1], 
            'red': row[2]
        })
    
    conn.close()
    
    print(f"\n=== INSTITUCIONES DISPONIBLES PARA BÚSQUEDA ===")
    print(f"Total con código modular: {len(todas_instituciones)}")
    
    # Mostrar por red
    df_ie = pd.DataFrame(todas_instituciones)
    if len(df_ie) > 0:
        print("\nDistribución por red:")
        red_counts = df_ie['red'].value_counts()
        for red, count in red_counts.items():
            print(f"  Red {red}: {count} instituciones")
    
    # 3. Ver resultados encontrados en SIAGIE
    try:
        df_siagie = pd.read_csv('historico_siagie_fya_2019_2024.csv')
        codigos_encontrados = set(df_siagie['codigo_modular'].unique())
        print(f"\n=== RESULTADOS SIAGIE ===")
        print(f"Instituciones ENCONTRADAS: {len(codigos_encontrados)}")
        print(f"Total registros académicos: {len(df_siagie)}")
        
        # Ver qué códigos se encontraron
        codigos_disponibles = set([inst['codigo_modular'] for inst in todas_instituciones])
        
        print(f"\n=== ANÁLISIS DETALLADO ===")
        print(f"Códigos disponibles en BD: {len(codigos_disponibles)}")
        print(f"Códigos encontrados en SIAGIE: {len(codigos_encontrados)}")
        print(f"Intersección (encontrados): {len(codigos_encontrados & codigos_disponibles)}")
        
        # Tasa de éxito real
        tasa_exito = (len(codigos_encontrados) / len(codigos_disponibles)) * 100
        print(f"TASA DE ÉXITO REAL: {tasa_exito:.1f}%")
        
        # Ver cuáles NO se encontraron
        no_encontrados = codigos_disponibles - codigos_encontrados
        print(f"\nCódigos NO encontrados en SIAGIE: {len(no_encontrados)}")
        
        if len(no_encontrados) > 0:
            print("Primeros códigos no encontrados:")
            for i, codigo in enumerate(sorted(list(no_encontrados))[:10]):
                inst = next((x for x in todas_instituciones if x['codigo_modular'] == codigo), None)
                if inst:
                    print(f"  {codigo}: {inst['nombre'][:40]}... (Red {inst['red']})")
        
        # Ver distribución de encontrados por red
        df_encontrados = df_siagie.groupby('red_fya').agg({
            'codigo_modular': 'nunique',
            'alumnos': 'sum'
        }).reset_index()
        
        print(f"\n=== INSTITUCIONES ENCONTRADAS POR RED ===")
        for _, row in df_encontrados.iterrows():
            print(f"Red {row['red_fya']}: {row['codigo_modular']} instituciones, {int(row['alumnos'])} alumnos")
        
    except FileNotFoundError:
        print("ERROR: No se encontró el archivo historico_siagie_fya_2019_2024.csv")
        
    return {
        'total_bd': total_ie,
        'con_codigo': con_codigo,
        'disponibles': len(todas_instituciones),
        'encontradas': len(codigos_encontrados) if 'codigos_encontrados' in locals() else 0
    }

if __name__ == "__main__":
    stats = verificar_cobertura()
    
    print(f"\n{'='*50}")
    print("RESUMEN FINAL:")
    print(f"Total IE en proyecto: {stats['total_bd']}")
    print(f"IE con código modular: {stats['con_codigo']}")
    print(f"IE encontradas en SIAGIE: {stats['encontradas']}")
    print(f"COBERTURA: {(stats['encontradas']/stats['con_codigo']*100):.1f}%")