#!/usr/bin/env python3
"""
Paso 21: Vinculador de Estudiantes usando Tabla de Mapeo - Proyecto Reasis
Añade y puebla la columna 'codigo_modular_vinculado' en la tabla de estudiantes
usando la tabla 'mapeo_codigos_ie' como puente.
"""

import pandas as pd
import re
import sqlite3

DB_PATH = 'reasis_database.db'

def vincular_con_mapeo():
    """
    Actualiza la tabla de estudiantes con el código modular correcto,
    obtenido a través de la tabla de mapeo.
    """
    print("--- INICIANDO PASO 21: VINCULACIÓN PERMANENTE VÍA TABLA DE MAPEO ---")
    print("=" * 75)

    conn = sqlite3.connect(DB_PATH)
    try:
        # 1. Cargar la tabla completa de estudiantes
        df_estudiantes = pd.read_sql_query("SELECT * FROM competencia_digital_estudiantes", conn)
        print(f"✅ Tabla de estudiantes cargada con {len(df_estudiantes)} registros.")

        # 2. Añadir la columna de vinculación si no existe
        if 'codigo_modular_vinculado' not in df_estudiantes.columns:
            df_estudiantes['codigo_modular_vinculado'] = None
            print("✅ Columna 'codigo_modular_vinculado' añadida al DataFrame.")

        # 3. Crear el diccionario de mapeo (misma lógica que la simulación)
        df_mapeo = pd.read_sql_query("SELECT nombre_ie_encontrado, codigo_modular FROM mapeo_codigos_ie", conn)
        mapa_dict = {}
        for _, row in df_mapeo.iterrows():
            match = re.search(r'(\d+)', str(row['nombre_ie_encontrado']))
            if match:
                mapa_dict[match.group(1)] = row['codigo_modular']
        print(f"✅ Diccionario de mapeo creado con {len(mapa_dict)} entradas.")

        # 4. Aplicar la vinculación en el DataFrame
        def buscar_vinculo(codigo_local_str):
            if pd.isna(codigo_local_str):
                return None
            match = re.search(r'(\d+)', str(codigo_local_str))
            if match:
                codigo_a_buscar = match.group(1)
                return mapa_dict.get(codigo_a_buscar) # Devuelve el código modular o None si no lo encuentra
            return None

        df_estudiantes['codigo_modular_vinculado'] = df_estudiantes['codigo_local'].apply(buscar_vinculo)
        vinculados = df_estudiantes['codigo_modular_vinculado'].notna().sum()
        print(f"✅ Vinculación aplicada en memoria. {vinculados} registros vinculados.")

        # 5. Reemplazar la tabla en la base de datos con los datos actualizados
        print("💾 Guardando tabla actualizada en la base de datos (esto puede tardar un momento)...")
        df_estudiantes.to_sql('competencia_digital_estudiantes', conn, if_exists='replace', index=False)
        print("✅ Tabla reemplazada con éxito.")

        # 6. Reporte final
        tasa_exito = (vinculados / len(df_estudiantes)) * 100 if len(df_estudiantes) > 0 else 0
        print("\n--- REPORTE DE VINCULACIÓN FINAL ---")
        print(f"Total de registros de estudiantes: {len(df_estudiantes)}")
        print(f"Registros vinculados a una institución: {vinculados}")
        print(f"Tasa de vinculación final: {tasa_exito:.1f}%")

    except Exception as e:
        print(f"❌ Ocurrió un error durante la vinculación: {e}")
    finally:
        conn.close()

    print("\n" + "=" * 75)

if __name__ == "__main__":
    vincular_con_mapeo()