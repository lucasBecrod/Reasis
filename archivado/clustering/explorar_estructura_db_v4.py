#!/usr/bin/env python3
"""
Explorar estructura de la base de datos reasis_database_v4.db
"""

import sqlite3
import pandas as pd

def explorar_tablas():
    """Explorar qué tablas existen en la DB"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    # Obtener lista de tablas
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = cursor.fetchall()
    
    print("=== TABLAS DISPONIBLES EN reasis_database_v4.db ===")
    for tabla in tablas:
        print(f"  {tabla[0]}")
    
    print("\n" + "=" * 60)
    
    # Para cada tabla, mostrar estructura
    for tabla in tablas:
        nombre_tabla = tabla[0]
        print(f"\n=== ESTRUCTURA TABLA: {nombre_tabla} ===")
        
        try:
            # Obtener información de columnas
            cursor.execute(f"PRAGMA table_info({nombre_tabla})")
            columnas = cursor.fetchall()
            
            print(f"Total columnas: {len(columnas)}")
            print("Columnas disponibles:")
            for col in columnas:
                print(f"  {col[1]} ({col[2]})")
            
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {nombre_tabla}")
            total_registros = cursor.fetchone()[0]
            print(f"Total registros: {total_registros}")
            
            # Mostrar muestra de datos si es tabla instituciones_educativas
            if nombre_tabla == 'instituciones_educativas':
                print("\nMuestra de primeros 3 registros:")
                df_sample = pd.read_sql_query(f"SELECT * FROM {nombre_tabla} LIMIT 3", conn)
                print(df_sample.to_string())
                
        except Exception as e:
            print(f"Error explorando tabla {nombre_tabla}: {e}")
    
    conn.close()

if __name__ == "__main__":
    explorar_tablas()