#!/usr/bin/env python3
"""
Paso 18: Diagnóstico de Códigos Modulares - Proyecto Reasis
Compara los códigos de los estudiantes con la columna 'codigo_modular' de
la tabla de instituciones para validar la nueva hipótesis de vinculación.
"""

import pandas as pd
import re
import sqlite3

DB_PATH = 'reasis_database.db'

def diagnosticar_codigos_modulares():
    """
    Extrae, compara y reporta las diferencias entre los códigos de estudiantes
    y los códigos modulares de las instituciones.
    """
    print("--- INICIANDO PASO 18: DIAGNÓSTICO DE CÓDIGOS MODULARES ---")
    print("=" * 65)

    conn = sqlite3.connect(DB_PATH)

    # 1. Extraer códigos de la tabla de estudiantes (misma lógica que antes)
    df_estudiantes = pd.read_sql_query("SELECT DISTINCT codigo_local FROM competencia_digital_estudiantes WHERE codigo_local IS NOT NULL AND codigo_local != ''", conn)
    student_codes = set()
    for code_str in df_estudiantes['codigo_local']:
        match = re.match(r'^(\d+)', str(code_str).strip())
        if match:
            student_codes.add(match.group(1))
    print(f"Códigos numéricos únicos extraídos de estudiantes: {len(student_codes)}")

    # 2. Extraer códigos MODULARES de la tabla de instituciones
    df_instituciones = pd.read_sql_query("SELECT DISTINCT codigo_modular FROM instituciones_educativas WHERE codigo_modular IS NOT NULL AND codigo_modular != ''", conn)
    institution_modular_codes = set(df_instituciones['codigo_modular'].astype(str).str.strip())
    print(f"Códigos MODULARES únicos en tabla de instituciones: {len(institution_modular_codes)}")

    # 3. Comparar ambos conjuntos de códigos
    matching_codes = student_codes.intersection(institution_modular_codes)
    student_codes_not_in_institutions = student_codes - institution_modular_codes

    print("\n--- RESULTADO DEL DIAGNÓSTICO (vs. CÓDIGO MODULAR) ---")
    print(f"Coincidencias encontradas: {len(matching_codes)}")
    
    if matching_codes:
        print(f"Ejemplos de códigos coincidentes: {list(matching_codes)[:20]}")

    if len(matching_codes) > 0:
        print("\n✅ CONCLUSIÓN: ¡Hipótesis confirmada! Los códigos de los estudiantes son en realidad 'códigos modulares'.")
        print("Siguiente paso: Actualizar el script de vinculación para usar 'codigo_modular' como clave.")
    else:
        print("\n⚠️ CONCLUSIÓN: Los códigos de los estudiantes tampoco coinciden con 'codigo_modular'. Se necesita una nueva estrategia.")

    conn.close()

if __name__ == "__main__":
    diagnosticar_codigos_modulares()