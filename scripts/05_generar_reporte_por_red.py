#!/usr/bin/env python3
"""
Paso 5: Generador de Reporte por Red - Proyecto Reasis
Crea un reporte consolidado en Markdown con métricas clave por red educativa.
"""

import pandas as pd
import sqlite3

DB_PATH = 'reasis_database.db'

def generar_reporte_consolidado():
    """
    Ejecuta una consulta SQL para unir las tablas principales y generar
    un reporte en formato Markdown.
    """
    print("--- INICIANDO PASO 5: GENERACIÓN DE REPORTE CONSOLIDADO POR RED ---")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)

    query = """
    WITH ILA_por_IE AS (
        SELECT
            codigo_modular,
            AVG(nivel_logro_numerico) as ila_promedio
        FROM resultados_academicos
        WHERE codigo_modular IS NOT NULL AND nivel_logro_numerico IS NOT NULL
        GROUP BY codigo_modular
    )
    SELECT
        r.lugar AS "Red",
        COUNT(DISTINCT ie.codigo_modular) AS "Instituciones",
        COUNT(DISTINCT d.dni) AS "Docentes Únicos",
        COUNT(DISTINCT ra.estudiante_id) AS "Estudiantes",
        ROUND(AVG(ila.ila_promedio), 2) AS "ILA Promedio"
    FROM redes_fe_y_alegria r
    LEFT JOIN instituciones_educativas ie ON r.codigo_red = ie.codigo_red
    LEFT JOIN docentes_data d ON ie.codigo_modular = d.codigo_modular_vinculado
    LEFT JOIN resultados_academicos ra ON ie.codigo_modular = ra.codigo_modular
    LEFT JOIN ILA_por_IE ila ON ie.codigo_modular = ila.codigo_modular
    GROUP BY r.codigo_red, r.lugar
    ORDER BY "Instituciones" DESC;
    """

    try:
        reporte_df = pd.read_sql_query(query, conn)
        print("✅ Consulta ejecutada exitosamente.")
    except Exception as e:
        print(f"❌ Error al ejecutar la consulta: {e}")
        conn.close()
        return

    conn.close()

    # Convertir a Markdown
    markdown_report = reporte_df.to_markdown(index=False)

    print("\n--- REPORTE CONSOLIDADO POR RED EDUCATIVA ---")
    print("Este reporte resume los recursos y el rendimiento académico por cada red.")
    print("Puedes copiar y pegar esta tabla en tus documentos (ej. AGENTS.md).\n")
    print(markdown_report)
    print("\n" + "=" * 70)
    print("✅ REPORTE GENERADO EXITOSAMENTE.")
    print("=" * 70)

def main():
    try:
        generar_reporte_consolidado()
    except Exception as e:
        print(f"\n❌ Ocurrió un error inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()