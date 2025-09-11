'''
Temporal script to test ILA calculation.
'''
import sqlite3
import pandas as pd
import numpy as np

def test_ila_calc():
    db_path = 'reasis_database.db'
    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)

    try:
        print("Cargando datos de 'resultados_academicos'...")
        materias = ['Matemática', 'Comunicación', 'Producción de textos']
        df = pd.read_sql_query(f"SELECT codigo_modular, materia, nivel_logro_numerico FROM resultados_academicos WHERE materia IN {tuple(materias)}", conn)
        print(f"Se cargaron {len(df)} registros relevantes.")

        # Calcular promedios por materia y por institución
        df_promedios = df.groupby(['codigo_modular', 'materia'])['nivel_logro_numerico'].mean().unstack()
        
        # Renombrar columnas para claridad
        df_promedios.rename(columns={'Matemática': 'avg_matematica', 'Comunicación': 'avg_comunicacion', 'Producción de textos': 'avg_produccion'}, inplace=True)

        # Reemplazar promedios de 0 con NaN para que no se incluyan en el cálculo final
        df_promedios.replace(0, np.nan, inplace=True)

        # Calcular Y1_ILA usando nanmean, que promedia ignorando NaN (valores faltantes o ceros)
        avg_cols = ['avg_matematica', 'avg_comunicacion', 'avg_produccion']
        df_promedios['Y1_ILA'] = df_promedios[avg_cols].apply(lambda x: np.nanmean(x[x.notna()]), axis=1)

        print("\nVista previa de los ILA calculados:")
        print(df_promedios.head())

    except Exception as e:
        print(f"Ocurrió un error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_ila_calc()