#!/usr/bin/env python3
"""
Paso 15.A: Explorador de la tabla de Instituciones - Proyecto Reasis
Muestra la estructura y datos clave de 'instituciones_educativas' para
validar la estrategia de vinculación con los estudiantes.
"""

import pandas as pd
import sqlite3

DB_PATH = 'reasis_database.db'

def explorar_tabla_instituciones():
    """
    Muestra el esquema y una muestra de los datos de la tabla de instituciones.
    """
    print("--- INICIANDO PASO 15.A: EXPLORACIÓN DE 'instituciones_educativas' ---")
    print("=" * 75)

    conn = sqlite3.connect(DB_PATH)
    try:
        # 1. Mostrar la estructura de la tabla
        print("\n--- ESTRUCTURA DE LA TABLA (PRAGMA table_info) ---")
        schema = pd.read_sql_query("PRAGMA table_info(instituciones_educativas);", conn)
        print(schema.to_string())

        # 2. Mostrar una muestra de los datos clave para la vinculación
        print("\n\n--- MUESTRA DE DATOS CLAVE PARA VINCULACIÓN ---")
        columnas_clave = ['codigo_modular', 'codigo_local', 'nombre_institucion', 'nivel_educativo']
        df_muestra = pd.read_sql_query(f"SELECT {', '.join(columnas_clave)} FROM instituciones_educativas LIMIT 10;", conn)
        
        print("Primeras 10 filas de columnas relevantes:")
        print(df_muestra.to_string(index=False))
        
        print("\n\n--- ANÁLISIS DE 'nivel_educativo' ---")
        niveles = pd.read_sql_query("SELECT DISTINCT nivel_educativo FROM instituciones_educativas;", conn)
        print("Valores únicos encontrados en 'nivel_educativo':")
        print(niveles['nivel_educativo'].to_list())

        print("\n✅ Exploración completada. Verifica que 'codigo_local' y 'nivel_educativo' son los correctos para la vinculación.")

    except Exception as e:
        print(f"❌ Ocurrió un error durante la exploración: {e}")
    finally:
        conn.close()

    print("\n" + "=" * 75)

if __name__ == "__main__":
    explorar_tabla_instituciones()