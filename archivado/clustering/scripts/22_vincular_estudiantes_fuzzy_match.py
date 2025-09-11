#!/usr/bin/env python3
"""
Paso 22: Vinculador de Estudiantes por Fuzzy Matching - Proyecto Reasis
Intenta vincular los registros restantes usando similitud de nombres.
"""

import pandas as pd
import re
import sqlite3
from difflib import get_close_matches

DB_PATH = 'reasis_database.db'

def vincular_fuzzy_matching():
    """
    Aplica una estrategia de fuzzy matching para vincular estudiantes
    que no pudieron ser vinculados por código.
    """
    print("--- INICIANDO PASO 22: VINCULACIÓN POR SIMILITUD DE NOMBRES (FUZZY MATCHING) ---")
    print("=" * 85)

    conn = sqlite3.connect(DB_PATH)
    try:
        # 1. Cargar solo los estudiantes NO vinculados
        df_sin_vincular = pd.read_sql_query("SELECT * FROM competencia_digital_estudiantes WHERE codigo_modular_vinculado IS NULL", conn)
        if df_sin_vincular.empty:
            print("✅ No hay estudiantes sin vincular. Proceso finalizado.")
            return

        print(f"🔍 Se encontraron {len(df_sin_vincular)} estudiantes sin vincular para procesar.")

        # 2. Cargar los nombres de las instituciones para comparar
        df_instituciones = pd.read_sql_query("SELECT codigo_modular, nombre_institucion FROM instituciones_educativas", conn)
        nombres_instituciones = df_instituciones['nombre_institucion'].str.upper().str.strip().tolist()
        mapa_nombres_a_modulares = pd.Series(df_instituciones.codigo_modular.values, index=df_instituciones.nombre_institucion.str.upper().str.strip()).to_dict()

        # 3. Aplicar Fuzzy Matching
        vinculados_fuzzy = 0
        for index, row in df_sin_vincular.iterrows():
            # Extraer solo la parte de texto del nombre del colegio
            nombre_estudiante_str = str(row['codigo_local'])
            nombre_a_buscar = re.sub(r'^\d+\s*', '', nombre_estudiante_str).strip().upper()

            if not nombre_a_buscar:
                continue

            # Encontrar la mejor coincidencia con una similitud alta (85%)
            mejores_coincidencias = get_close_matches(nombre_a_buscar, nombres_instituciones, n=1, cutoff=0.85)

            if mejores_coincidencias:
                nombre_encontrado = mejores_coincidencias[0]
                codigo_modular_encontrado = mapa_nombres_a_modulares.get(nombre_encontrado)
                
                # Actualizar el registro en la base de datos
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE competencia_digital_estudiantes SET codigo_modular_vinculado = ? WHERE id = ?",
                    (codigo_modular_encontrado, row['id'])
                )
                vinculados_fuzzy += 1

        conn.commit()
        print(f"✅ Proceso de Fuzzy Matching finalizado. Se vincularon {vinculados_fuzzy} registros adicionales.")

        # 4. Reporte final
        total_registros = pd.read_sql_query("SELECT COUNT(*) FROM competencia_digital_estudiantes", conn).iloc[0, 0]
        vinculados_ahora = pd.read_sql_query("SELECT COUNT(*) FROM competencia_digital_estudiantes WHERE codigo_modular_vinculado IS NOT NULL", conn).iloc[0, 0]
        tasa_exito_final = (vinculados_ahora / total_registros) * 100 if total_registros > 0 else 0

        print("\n--- REPORTE DE VINCULACIÓN ACTUALIZADO ---")
        print(f"Total de registros de estudiantes: {total_registros}")
        print(f"Registros vinculados ahora: {vinculados_ahora}")
        print(f"Nueva tasa de vinculación final: {tasa_exito_final:.1f}%")

    except Exception as e:
        print(f"❌ Ocurrió un error durante la vinculación fuzzy: {e}")
        print("   Asegúrate de que la tabla 'competencia_digital_estudiantes' tenga una columna 'id'.")
    finally:
        conn.close()

    print("\n" + "=" * 85)

if __name__ == "__main__":
    vincular_fuzzy_matching()