#!/usr/bin/env python3
"""
Paso 15: Explorador de Vinculación Estudiantes <-> Instituciones - Proyecto Reasis
Evalúa la viabilidad de vincular 'competencia_digital_estudiantes' con
'instituciones_educativas' usando las columnas 'colegio' y 'nivel'.
"""

import pandas as pd
import re
import sqlite3

DB_PATH = 'reasis_database.db'

def explorar_vinculacion_estudiantes():
    """
    Analiza el contenido de la columna 'colegio' y simula la vinculación
    para determinar la tasa de éxito potencial.
    """
    print("--- INICIANDO PASO 15: EXPLORACIÓN DE VINCULACIÓN ESTUDIANTES-IE ---")
    print("=" * 75)

    conn = sqlite3.connect(DB_PATH)
    try:
        # Cargar los datos necesarios
        df_estudiantes = pd.read_sql_query("SELECT codigo_local, nivel FROM competencia_digital_estudiantes", conn)
        df_instituciones = pd.read_sql_query("SELECT id as institucion_id, codigo_local, codigo_modular, nivel_educativo FROM instituciones_educativas", conn)
        print(f"✅ Datos cargados: {len(df_estudiantes)} registros de estudiantes y {len(df_instituciones)} de instituciones.")

        # 1. Analizar la columna 'codigo_local'
        df_con_codigo = df_estudiantes[df_estudiantes['codigo_local'].notna() & (df_estudiantes['codigo_local'] != '')].copy()
        total_con_codigo = len(df_con_codigo)
        porcentaje = (total_con_codigo / len(df_estudiantes)) * 100 if len(df_estudiantes) > 0 else 0

        print("\n--- ANÁLISIS DE LA COLUMNA 'codigo_local' ---")
        print(f"Registros con valor en 'codigo_local': {total_con_codigo} de {len(df_estudiantes)} ({porcentaje:.1f}%)")

        if total_con_codigo == 0:
            print("⚠️ No hay datos en la columna 'colegio' para intentar la vinculación. Proceso detenido.")
            return

        print("\nMostrando 5 valores de ejemplo de la columna 'codigo_local':")
        print(df_con_codigo['codigo_local'].head().to_list())

        # 2. Simular la vinculación
        print("\n--- SIMULACIÓN DE VINCULACIÓN ---")
        print("Estrategia: Extraer el número de 'colegio' y compararlo con 'codigo_local'.")

        vinculados_exitosamente = 0
        no_vinculados = 0

        # Convertir a string para asegurar la comparación
        df_instituciones['codigo_local'] = df_instituciones['codigo_local'].astype(str).str.strip()

        for _, row in df_con_codigo.iterrows():
            # Extraer solo la parte numérica del inicio del campo 'colegio'
            match_codigo = re.match(r'^(\d+)', str(row['codigo_local']).strip())
            if not match_codigo:
                no_vinculados += 1
                continue
            codigo_local_est = match_codigo.group(1)
            nivel_est = str(row['nivel']).upper()

            # Buscar coincidencias
            match = df_instituciones[
                (df_instituciones['codigo_local'] == codigo_local_est) &
                (df_instituciones['nivel_educativo'].str.upper().str.contains(nivel_est, na=False))
            ]

            if not match.empty:
                vinculados_exitosamente += 1
            else:
                no_vinculados += 1

        print("\n--- RESULTADOS DE LA SIMULACIÓN ---")
        tasa_exito = (vinculados_exitosamente / total_con_codigo) * 100 if total_con_codigo > 0 else 0
        print(f"Registros que se pueden vincular: {vinculados_exitosamente} de {total_con_codigo}")
        print(f"Registros no vinculados: {no_vinculados}")
        print(f"Tasa de éxito potencial: {tasa_exito:.1f}%")

        if tasa_exito > 70:
            print("\n✅ CONCLUSIÓN: La estrategia es viable. Se puede proceder a la implementación.")
        else:
            print("\n⚠️ CONCLUSIÓN: La tasa de éxito es baja. Se recomienda revisar la estrategia o buscar campos alternativos.")

    except Exception as e:
        print(f"❌ Ocurrió un error durante la exploración: {e}")
    finally:
        conn.close()

    print("\n" + "=" * 75)

if __name__ == "__main__":
    explorar_vinculacion_estudiantes()