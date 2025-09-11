#!/usr/bin/env python3
"""
Verificar columnas disponibles en tabla instituciones_educativas
"""

import sqlite3
import pandas as pd

def main():
    print("=== VERIFICANDO ESTRUCTURA DE TABLA INSTITUCIONES_EDUCATIVAS ===")
    
    conn = sqlite3.connect('reasis_database.db')
    
    try:
        # Ver todas las tablas
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = cursor.fetchall()
        print("Tablas disponibles:")
        for tabla in tablas:
            print(f"  - {tabla[0]}")
        
        # Ver columnas de instituciones_educativas
        print(f"\nColumnas en tabla 'instituciones_educativas':")
        cursor.execute("PRAGMA table_info(instituciones_educativas);")
        columnas = cursor.fetchall()
        
        for col in columnas:
            print(f"  - {col[1]} ({col[2]})")
        
        # Mostrar muestra de datos
        print(f"\nMuestra de datos (primeras 3 filas):")
        df_muestra = pd.read_sql_query("SELECT * FROM instituciones_educativas LIMIT 3", conn)
        print(df_muestra.to_string())
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()