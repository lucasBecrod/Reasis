#!/usr/bin/env python3
"""
Paso 19: Explorador de la Tabla de Mapeo de Códigos - Proyecto Reasis
Muestra la estructura y datos de la tabla 'mapeo_codigos_ie' para
diseñar la estrategia de vinculación de estudiantes.
"""

import pandas as pd
import sqlite3

DB_PATH = 'reasis_database.db'

def explorar_mapeo_codigos():
    """
    Muestra la estructura y datos de la tabla 'mapeo_codigos_ie'
    para diseñar la estrategia de vinculación.
    """
    print("--- INICIANDO PASO 19: EXPLORACIÓN DE LA TABLA 'mapeo_codigos_ie' ---")
    print("=" * 75)

    conn = sqlite3.connect(DB_PATH)
    try:
        # 1. Verificar si la tabla existe
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mapeo_codigos_ie'")
        if cursor.fetchone() is None:
            print("❌ ERROR: La tabla 'mapeo_codigos_ie' no existe en la base de datos.")
            print("   Esta tabla se crea durante la vinculación de 'resultados_academicos'.")
            print("   Asegúrate de que ese proceso se haya ejecutado correctamente.")
            return

        # 2. Mostrar la estructura de la tabla
        print("\n--- ESTRUCTURA DE LA TABLA (PRAGMA table_info) ---")
        schema = pd.read_sql_query("PRAGMA table_info(mapeo_codigos_ie);", conn)
        print(schema.to_string())

        # 3. Mostrar una muestra de los datos
        print("\n\n--- MUESTRA DE DATOS DE 'mapeo_codigos_ie' ---")
        df_muestra = pd.read_sql_query("SELECT * FROM mapeo_codigos_ie LIMIT 15;", conn)
        
        print("Primeras 15 filas de la tabla de mapeo:")
        print(df_muestra.to_string(index=False))

        print("\n\n--- ANÁLISIS Y ESTRATEGIA PROPUESTA ---")
        print("La tabla 'mapeo_codigos_ie' actúa como un diccionario que traduce los códigos internos")
        print("de los archivos Excel (en la columna 'codigo_local') al 'codigo_modular' oficial.")
        print("\nNUEVA ESTRATEGIA DE VINCULACIÓN:")
        print("1. Extraer el código numérico de la columna 'codigo_local' de la tabla de estudiantes.")
        print("2. Buscar ese código numérico en la columna 'codigo_local' de la tabla 'mapeo_codigos_ie'.")
        print("3. Si se encuentra una coincidencia, obtener el 'codigo_modular' correspondiente de esa misma fila.")
        print("4. Usar ese 'codigo_modular' para vincular al estudiante con la institución correcta.")
        print("\nEsta estrategia es prometedora porque reutiliza la lógica que ya funcionó para los resultados académicos.")

    except Exception as e:
        print(f"❌ Ocurrió un error durante la exploración: {e}")
    finally:
        conn.close()

    print("\n" + "=" * 75)

if __name__ == "__main__":
    explorar_mapeo_codigos()