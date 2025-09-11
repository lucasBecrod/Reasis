import sqlite3
import pandas as pd
import numpy as np

def calcular_y1_ila_preciso():
    '''
    Script para calcular el Índice de Logro Académico (Y1_ILA) de forma precisa,
    considerando las materias de Matemática, Comunicación y Producción de textos.

    Metodología:
    1. Se conecta a la base de datos 'reasis_database.db'.
    2. Lee los datos de 'resultados_academicos' para las tres materias clave.
    3. Para cada institución (codigo_modular), calcula el promedio por separado para cada materia.
    4. Calcula el ILA final promediando únicamente los promedios de materia que se pudieron calcular y que no son cero.
    5. Actualiza la columna 'Y1_ILA' en la tabla 'indices_metodologicos'.
    '''
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

        # Actualizar la tabla indices_metodologicos
        print("\nActualizando la tabla 'indices_metodologicos'...")
        update_count = 0
        for codigo_modular, row in df_promedios.iterrows():
            ila_value = row['Y1_ILA']
            if pd.notna(ila_value):
                cursor = conn.cursor()
                update_query = "UPDATE indices_metodologicos SET Y1_ILA = ? WHERE codigo_modular = ?"
                cursor.execute(update_query, (ila_value, codigo_modular))
                update_count += cursor.rowcount
        
        conn.commit()
        print(f"Se actualizaron {update_count} registros en 'indices_metodologicos'.")

        # Verificación
        print("\nVerificando los primeros 5 registros actualizados:")
        df_verificacion = pd.read_sql_query("SELECT codigo_modular, nombre_institucion, Y1_ILA FROM indices_metodologicos WHERE Y1_ILA IS NOT NULL LIMIT 5", conn)
        print(df_verificacion)

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    calcular_y1_ila_preciso()
