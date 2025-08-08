#!/usr/bin/env python3
"""
Paso 13: Analizador de Competencias Digitales de Estudiantes por Red - Proyecto Reasis
Calcula y muestra el promedio de las competencias digitales para cada red educativa.
"""

import pandas as pd
import sqlite3

DB_PATH = 'reasis_database.db'

def analizar_competencias_estudiantes_por_red():
    """
    Consulta la tabla de competencias de estudiantes, calcula los promedios por red
    y muestra un reporte en formato Markdown.
    """
    print("--- INICIANDO PASO 13: ANÁLISIS DE COMPETENCIAS DE ESTUDIANTES POR RED ---")
    print("=" * 75)

    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT
        r.lugar AS "Red",
        COUNT(c.año) AS "Estudiantes Evaluados",
        ROUND(AVG(c.competencia_digital_num), 2) AS "Prom. Comp. Digital",
        ROUND(AVG(c.pensamiento_computacional_num), 2) AS "Prom. Pens. Comp.",
        ROUND(AVG(c.ciudadania_digital_num), 2) AS "Prom. Ciudad. Digital",
        ROUND(AVG(c.nota_global_num), 2) AS "Prom. Nota Global"
    FROM competencia_digital_estudiantes c
    JOIN redes_fe_y_alegria r ON c.codigo_red = r.codigo_red
    WHERE c.nota_global_num IS NOT NULL
    GROUP BY c.codigo_red, r.lugar
    ORDER BY "Prom. Nota Global" DESC;
    """

    try:
        reporte_df = pd.read_sql_query(query, conn)
        print("✅ Consulta de análisis ejecutada exitosamente.")
    except Exception as e:
        print(f"❌ Error al ejecutar la consulta de análisis: {e}")
        return
    finally:
        conn.close()

    # Convertir a Markdown
    markdown_report = reporte_df.to_markdown(index=False)

    print("\n--- REPORTE DE COMPETENCIAS DIGITALES PROMEDIO DE ESTUDIANTES POR RED ---")
    print("Escala de Promedio: 1 (Inicio), 2 (En Proceso), 3 (Logrado)\n")
    print(markdown_report)
    print("\n" + "=" * 75)
    print("✅ REPORTE GENERADO EXITOSAMENTE.")
    print("=" * 75)

if __name__ == "__main__":
    try:
        analizar_competencias_estudiantes_por_red()
    except Exception as e:
        print(f"\n❌ Ocurrió un error inesperado: {e}")