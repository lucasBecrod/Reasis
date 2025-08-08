#!/usr/bin/env python3
"""
Paso 10: Visualizador de Competencias Digitales por Red - Proyecto Reasis
Crea un gráfico de barras para comparar la Nota Global Promedio de cada red.
"""

import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns

DB_PATH = 'reasis_database.db'

def visualizar_competencias_por_red():
    """
    Genera y muestra un gráfico de barras comparando la nota global promedio por red.
    """
    print("--- INICIANDO PASO 10: VISUALIZACIÓN DE COMPETENCIAS DIGITALES POR RED ---")
    print("=" * 75)

    conn = sqlite3.connect(DB_PATH)

    # Consulta para obtener los datos necesarios para el gráfico
    query = """
    SELECT
        r.lugar AS "Red",
        ROUND(AVG(c.nota_global_relativa_num), 2) AS "Prom. Nota Global"
    FROM competencia_digital_docentes c
    JOIN redes_fe_y_alegria r ON c.codigo_red = r.codigo_red
    GROUP BY c.codigo_red, r.lugar
    ORDER BY "Prom. Nota Global" DESC;
    """

    try:
        reporte_df = pd.read_sql_query(query, conn)
        print("✅ Datos para el gráfico obtenidos exitosamente.")
    except Exception as e:
        print(f"❌ Error al obtener los datos: {e}")
        return
    finally:
        conn.close()

    # Creación del gráfico
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))

    bars = sns.barplot(x='Red', y='Prom. Nota Global', data=reporte_df, ax=ax, palette='plasma', hue='Red', legend=False)

    # Añadir etiquetas de valor sobre las barras
    for bar in bars.patches:
        ax.annotate(format(bar.get_height(), '.2f'),
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha='center', va='center',
                    size=10, xytext=(0, 8),
                    textcoords='offset points')

    ax.set_title('Competencia Digital Docente Promedio por Red', fontsize=16, weight='bold')
    ax.set_xlabel('Red Educativa', fontsize=12)
    ax.set_ylabel('Nota Global Promedio (Escala 1-4)', fontsize=12)
    ax.set_ylim(0, 4) # Escala fija de 1 a 4 para una comparación justa
    ax.axhline(2, color='gray', linestyle='--', linewidth=1)
    ax.text(len(reporte_df)-0.5, 2.05, 'Nivel "En Proceso"', color='gray', va='bottom', ha='right')
    plt.tight_layout()
    
    print("📊 Mostrando gráfico... Cierra la ventana del gráfico para continuar.")
    plt.show()
    print("✅ Gráfico mostrado exitosamente.")

if __name__ == "__main__":
    visualizar_competencias_por_red()