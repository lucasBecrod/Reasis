#!/usr/bin/env python3
"""
Paso 6: Visualizador de ILA por Red - Proyecto Reasis
Crea un gráfico de barras para comparar el ILA Promedio de cada red educativa.
"""

import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns

DB_PATH = 'reasis_database.db'

def visualizar_ila_por_red():
    """
    Genera y muestra un gráfico de barras comparando el ILA promedio por red.
    """
    print("--- INICIANDO PASO 6: VISUALIZACIÓN DE ILA PROMEDIO POR RED ---")
    print("=" * 65)

    conn = sqlite3.connect(DB_PATH)

    # Usamos la misma consulta robusta del script de reporte
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
        ROUND(AVG(ila.ila_promedio), 2) AS "ILA Promedio"
    FROM redes_fe_y_alegria r
    LEFT JOIN instituciones_educativas ie ON r.codigo_red = ie.codigo_red
    LEFT JOIN ILA_por_IE ila ON ie.codigo_modular = ila.codigo_modular
    WHERE ila.ila_promedio IS NOT NULL
    GROUP BY r.codigo_red, r.lugar
    ORDER BY "ILA Promedio" DESC;
    """

    try:
        reporte_df = pd.read_sql_query(query, conn)
        print("✅ Datos para el gráfico obtenidos exitosamente.")
    except Exception as e:
        print(f"❌ Error al obtener los datos: {e}")
        conn.close()
        return
    finally:
        conn.close()

    # Creación del gráfico
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))

    bars = sns.barplot(x='Red', y='ILA Promedio', data=reporte_df, ax=ax, palette='viridis')

    # Añadir etiquetas de valor sobre las barras
    for bar in bars.patches:
        ax.annotate(format(bar.get_height(), '.2f'),
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha='center', va='center',
                    size=10, xytext=(0, 8),
                    textcoords='offset points')

    ax.set_title('Comparación del Índice de Logro Académico (ILA) Promedio por Red', fontsize=16)
    ax.set_xlabel('Red Educativa', fontsize=12)
    ax.set_ylabel('ILA Promedio (Escala 1-4)', fontsize=12)
    ax.set_ylim(0, max(reporte_df['ILA Promedio']) * 1.2) # Ajustar límite para dar espacio a etiquetas
    plt.tight_layout()
    
    print("📊 Mostrando gráfico... Cierra la ventana del gráfico para continuar.")
    plt.show()
    print("✅ Gráfico mostrado exitosamente.")

if __name__ == "__main__":
    try:
        visualizar_ila_por_red()
    except ImportError:
        print("\n❌ Error: Faltan librerías para graficar.")
        print("   Por favor, instálalas ejecutando:")
        print("   pip install matplotlib seaborn")
    except Exception as e:
        print(f"\n❌ Ocurrió un error inesperado: {e}")