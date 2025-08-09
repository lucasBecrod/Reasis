#!/usr/bin/env python3
import sqlite3

def diagnosticar_base_datos():
    """Examina la estructura y contenido de la base de datos Reasis"""
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    print("=== DIAGNÓSTICO BASE DE DATOS REASIS ===\n")
    
    # Obtener todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [table[0] for table in cursor.fetchall() if table[0] != 'sqlite_sequence']
    
    print(f"Total de tablas: {len(tables)}\n")
    
    for table in tables:
        print(f"--- {table} ---")
        
        # Obtener estructura de la tabla
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        print(f"Columnas ({len(columns)}):")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Obtener conteo de registros
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"Total registros: {count}\n")
    
    conn.close()

if __name__ == "__main__":
    diagnosticar_base_datos()