#!/usr/bin/env python3
"""
Paso 20: Simulación de Vinculación usando Tabla de Mapeo - Proyecto Reasis
Evalúa la viabilidad de vincular estudiantes usando 'mapeo_codigos_ie' como puente.
"""

import pandas as pd
import re
import sqlite3

DB_PATH = 'reasis_database.db'

def simular_vinculacion_con_mapeo():
    """
    Simula la vinculación de estudiantes a instituciones usando la tabla de mapeo
    para predecir la tasa de éxito.
    """
    print("--- INICIANDO PASO 20: SIMULACIÓN DE VINCULACIÓN VÍA TABLA DE MAPEO ---")
    print("=" * 75)

    conn = sqlite3.connect(DB_PATH)
    try:
        # 1. Cargar los datos necesarios
        df_estudiantes = pd.read_sql_query("SELECT codigo_local FROM competencia_digital_estudiantes WHERE codigo_local IS NOT NULL AND codigo_local != ''", conn)
        df_mapeo = pd.read_sql_query("SELECT nombre_ie_encontrado, codigo_modular FROM mapeo_codigos_ie", conn)
        print(f"✅ Datos cargados: {len(df_estudiantes)} registros de estudiantes y {len(df_mapeo)} de mapeo.")

        # 2. Crear un diccionario de mapeo para búsquedas rápidas
        # La clave será el código extraído de 'nombre_ie_encontrado' y el valor será 'codigo_modular'
        mapa_dict = {}
        for _, row in df_mapeo.iterrows():
            nombre_encontrado = str(row['nombre_ie_encontrado'])
            codigo_modular = row['codigo_modular']
            # Extraer el primer grupo de números que encuentre
            match = re.search(r'(\d+)', nombre_encontrado)
            if match:
                codigo_mapeo = match.group(1)
                if codigo_mapeo not in mapa_dict: # Evitar sobreescribir con mapeos menos específicos
                    mapa_dict[codigo_mapeo] = codigo_modular
        print(f"✅ Diccionario de mapeo creado con {len(mapa_dict)} entradas únicas.")

        # 3. Simular la vinculación
        vinculados_exitosamente = 0
        for _, row in df_estudiantes.iterrows():
            codigo_estudiante_str = str(row['codigo_local'])
            # Extraer el código numérico del estudiante
            match = re.search(r'(\d+)', codigo_estudiante_str)
            if match:
                codigo_a_buscar = match.group(1)
                if codigo_a_buscar in mapa_dict:
                    vinculados_exitosamente += 1

        # 4. Reportar resultados de la simulación
        total_a_vincular = len(df_estudiantes)
        tasa_exito = (vinculados_exitosamente / total_a_vincular) * 100 if total_a_vincular > 0 else 0

        print("\n--- RESULTADOS DE LA SIMULACIÓN ---")
        print(f"Registros de estudiantes con código a vincular: {total_a_vincular}")
        print(f"Registros que se pueden vincular usando la tabla de mapeo: {vinculados_exitosamente}")
        print(f"Tasa de éxito potencial: {tasa_exito:.1f}%")

        if tasa_exito > 80:
            print("\n✅ CONCLUSIÓN: ¡Éxito! La estrategia de usar 'mapeo_codigos_ie' es altamente efectiva.")
        else:
            print("\n⚠️ CONCLUSIÓN: La estrategia funciona, pero la cobertura podría mejorarse. Aún así, es el mejor método hasta ahora.")

    except Exception as e:
        print(f"❌ Ocurrió un error durante la simulación: {e}")
    finally:
        conn.close()

    print("\n" + "=" * 75)

if __name__ == "__main__":
    simular_vinculacion_con_mapeo()