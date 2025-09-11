#!/usr/bin/env python3
"""
Paso 9: Analizador de Competencias Digitales por Red - Proyecto Reasis
Calcula y muestra el promedio de las competencias digitales para cada red educativa.
"""

import pandas as pd
import sqlite3

DB_PATH = 'reasis_database.db'

def analizar_competencias_por_red():
    """
    Consulta la tabla de competencias digitales, calcula los promedios por red
    y muestra un reporte en formato Markdown.
    """
    print("--- INICIANDO PASO 9: ANÁLISIS DE COMPETENCIAS DIGITALES POR RED ---")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        r.lugar AS "Red",
        COUNT(c.año) AS "Docentes Evaluados",
        ROUND(AVG(c.profesional_empoderado_num), 2) AS "Prom. Prof. Empoderado",
        ROUND(AVG(c.catalizador_aprendizaje_num), 2) AS "Prom. Catalizador",
        ROUND(AVG(c.nota_global_relativa_num), 2) AS "Prom. Nota Global"
    FROM competencia_digital_docentes c
    JOIN redes_fe_y_alegria r ON c.codigo_red = r.codigo_red
    GROUP BY c.codigo_red, r.lugar
    ORDER BY "Prom. Nota Global" DESC;
    """

    try:
        reporte_df = pd.read_sql_query(query, conn)
        print("✅ Consulta de análisis ejecutada exitosamente.")
    except Exception as e:
        print(f"❌ Error al ejecutar la consulta de análisis: {e}")
        conn.close()
        return
    finally:
        conn.close()

    # Convertir a Markdown
    markdown_report = reporte_df.to_markdown(index=False)

    print("\n--- REPORTE DE COMPETENCIAS DIGITALES PROMEDIO POR RED ---")
    print("Escala de Promedio: 1 (Básico) a 4 (Destacado)\n")
    print(markdown_report)
    print("\n" + "=" * 70)
    print("✅ REPORTE GENERADO EXITOSAMENTE.")
    print("=" * 70)

if __name__ == "__main__":
    try:
        analizar_competencias_por_red()
    except Exception as e:
        print(f"\n❌ Ocurrió un error inesperado: {e}")