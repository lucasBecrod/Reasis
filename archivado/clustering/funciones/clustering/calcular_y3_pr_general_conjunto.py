"""
Script para calcular Y3_PR general directamente desde la tabla resultados_academicos
Calcula el porcentaje de estudiantes en nivel satisfactorio/logrado/destacado por institución educativa
Autor: Proyecto Reasis
Fecha: 2025-08-10
"""
import sqlite3
import pandas as pd

def calcular_y3_pr_general():
    conn = sqlite3.connect('reasis_database.db')
    # Extraer todos los resultados académicos
    df = pd.read_sql_query("""
        SELECT codigo_modular, nivel_logro_texto
        FROM resultados_academicos
        WHERE nivel_logro_texto IS NOT NULL
    """, conn)
    # Normalizar códigos
    df['codigo_modular'] = df['codigo_modular'].apply(lambda x: str(int(float(x))) if pd.notna(x) else None)
    # Definir niveles satisfactorios
    niveles_ok = ['Satisfactorio', 'Logrado', 'Destacado']
    # Calcular por IIEE
    resumen = df.groupby('codigo_modular').agg(
        total_evaluados = ('nivel_logro_texto', 'count'),
        satisfactorio = ('nivel_logro_texto', lambda x: sum([v in niveles_ok for v in x]))
    )
    resumen['Y3_PR'] = resumen['satisfactorio'] / resumen['total_evaluados']
    resumen = resumen.reset_index()
    # Actualizar tabla indices_metodologicos
    cur = conn.cursor()
    actualizados = 0
    for _, row in resumen.iterrows():
        cur.execute("""
            UPDATE indices_metodologicos
            SET Y3_PR = ?
            WHERE CODIGO_MODULAR = ?
        """, (row['Y3_PR'], row['codigo_modular']))
        actualizados += cur.rowcount
    conn.commit()
    conn.close()
    print(f"Y3_PR aplicado a {actualizados} instituciones.")

if __name__ == "__main__":
    calcular_y3_pr_general()
