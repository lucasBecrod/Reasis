#!/usr/bin/env python3
"""
Paso 17: Diagnóstico de Códigos Locales - Proyecto Reasis
Compara los códigos locales de la tabla de estudiantes con los de la
tabla de instituciones para identificar la causa de la falla de vinculación.
"""

import pandas as pd
import re
import sqlite3

DB_PATH = 'reasis_database.db'

def diagnosticar_codigos():
    """
    Extrae, compara y reporta las diferencias entre los códigos locales de
    estudiantes e instituciones.
    """
    print("--- INICIANDO PASO 17: DIAGNÓSTICO DE CÓDIGOS LOCALES ---")
    print("=" * 65)

    conn = sqlite3.connect(DB_PATH)

    # 1. Extraer códigos de la tabla de estudiantes
    df_estudiantes = pd.read_sql_query("SELECT DISTINCT codigo_local FROM competencia_digital_estudiantes WHERE codigo_local IS NOT NULL AND codigo_local != ''", conn)
    student_codes = set()
    for code_str in df_estudiantes['codigo_local']:
        match = re.match(r'^(\d+)', str(code_str).strip())
        if match:
            student_codes.add(match.group(1))
    print(f"Códigos numéricos únicos extraídos de estudiantes: {len(student_codes)}")

    # 2. Extraer códigos de la tabla de instituciones
    df_instituciones = pd.read_sql_query("SELECT DISTINCT codigo_local FROM instituciones_educativas WHERE codigo_local IS NOT NULL AND codigo_local != ''", conn)
    institution_codes = set(df_instituciones['codigo_local'].astype(str).str.strip())
    print(f"Códigos locales únicos en tabla de instituciones: {len(institution_codes)}")

    # 3. Comparar ambos conjuntos de códigos
    matching_codes = student_codes.intersection(institution_codes)
    student_codes_not_in_institutions = student_codes - institution_codes

    print("\n--- RESULTADO DEL DIAGNÓSTICO ---")
    print(f"Coincidencias encontradas: {len(matching_codes)}")
    print(f"Códigos de estudiantes SIN coincidencia en instituciones: {len(student_codes_not_in_institutions)}")

    if student_codes_not_in_institutions:
        print(f"\nEjemplos de códigos de estudiantes que NO se encontraron: {list(student_codes_not_in_institutions)[:20]}")
        print("\nCONCLUSIÓN: La vinculación falla porque los códigos de los estudiantes no existen en la columna 'codigo_local' de las instituciones.")
        print("Siguiente paso: Investigar si estos códigos existen en otra columna (ej. 'codigo_modular').")
    else:
        print("\n✅ Todos los códigos de estudiantes existen en la tabla de instituciones. El problema podría estar en el cruce con el 'nivel' educativo.")

    conn.close()

if __name__ == "__main__":
    diagnosticar_codigos()