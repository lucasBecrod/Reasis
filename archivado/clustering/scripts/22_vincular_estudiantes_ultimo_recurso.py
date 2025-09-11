#!/usr/bin/env python3
"""
Paso 22: Vinculador de Estudiantes de Último Recurso - Proyecto Reasis
Intenta vincular los registros restantes usando la tabla de mapeo pero
sin el filtro de 'nivel', como estrategia final.
"""

import pandas as pd
import re
import sqlite3

DB_PATH = 'reasis_database.db'

def vincular_ultimo_recurso():
    """
    Aplica una estrategia de vinculación más flexible a los estudiantes
    que no pudieron ser vinculados previamente.
    """
    print("--- INICIANDO PASO 22: VINCULACIÓN DE ÚLTIMO RECURSO (SIN FILTRO DE NIVEL) ---")
    print("=" * 85)

    conn = sqlite3.connect(DB_PATH)
    try:
        # 1. Cargar la tabla completa de estudiantes
        df_estudiantes = pd.read_sql_query("SELECT * FROM competencia_digital_estudiantes", conn)
        vinculados_antes = df_estudiantes['codigo_modular_vinculado'].notna().sum()
        print(f"🔍 Registros cargados: {len(df_estudiantes)}. Vinculados previamente: {vinculados_antes}.")

        # 2. Crear el diccionario de mapeo (misma lógica que antes)
        df_mapeo = pd.read_sql_query("SELECT nombre_ie_encontrado, codigo_modular FROM mapeo_codigos_ie", conn)
        mapa_dict = {}
        for _, row in df_mapeo.iterrows():
            match = re.search(r'(\d+)', str(row['nombre_ie_encontrado']))
            if match:
                mapa_dict[match.group(1)] = row['codigo_modular']
        print(f"✅ Diccionario de mapeo creado con {len(mapa_dict)} entradas.")

        # 3. Aplicar la vinculación de último recurso
        def buscar_vinculo_flexible(row):
            # Si ya está vinculado, no lo tocamos
            if pd.notna(row['codigo_modular_vinculado']):
                return row['codigo_modular_vinculado']
            
            # Si no hay código local, no podemos hacer nada
            if pd.isna(row['codigo_local']):
                return None
            
            # Extraer el código numérico y buscar en el mapa
            match = re.search(r'(\d+)', str(row['codigo_local']))
            if match:
                codigo_a_buscar = match.group(1)
                return mapa_dict.get(codigo_a_buscar)
            return None

        df_estudiantes['codigo_modular_vinculado'] = df_estudiantes.apply(buscar_vinculo_flexible, axis=1)
        
        vinculados_ahora = df_estudiantes['codigo_modular_vinculado'].notna().sum()
        nuevos_vinculados = vinculados_ahora - vinculados_antes
        print(f"✅ Estrategia de último recurso aplicada. Se vincularon {nuevos_vinculados} registros adicionales.")

        # 4. Reemplazar la tabla en la base de datos
        print("💾 Guardando tabla actualizada en la base de datos...")
        df_estudiantes.to_sql('competencia_digital_estudiantes', conn, if_exists='replace', index=False)
        print("✅ Tabla reemplazada con éxito.")

        # 5. Reporte final
        tasa_exito_final = (vinculados_ahora / len(df_estudiantes)) * 100 if len(df_estudiantes) > 0 else 0
        print("\n--- REPORTE DE VINCULACIÓN FINAL ---")
        print(f"Total de registros de estudiantes: {len(df_estudiantes)}")
        print(f"Registros vinculados ahora: {vinculados_ahora}")
        print(f"Nueva tasa de vinculación final: {tasa_exito_final:.1f}%")

    except Exception as e:
        print(f"❌ Ocurrió un error durante la vinculación: {e}")
    finally:
        conn.close()

    print("\n" + "=" * 85)

if __name__ == "__main__":
    vincular_ultimo_recurso()