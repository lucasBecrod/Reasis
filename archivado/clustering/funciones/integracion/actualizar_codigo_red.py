'''
Script para actualizar la columna 'codigo_red' en la tabla 'resultados_academicos'
usando los dos primeros dígitos de la columna 'region'.

Este script realiza las siguientes acciones:
1. Se conecta a la base de datos SQLite 'reasis_database.db'.
2. Carga la tabla 'resultados_academicos' en un DataFrame de pandas.
3. Extrae los dos primeros caracteres de la columna 'region' para cada fila.
4. Actualiza la columna 'codigo_red' con estos nuevos valores.
5. Guarda el DataFrame modificado de nuevo en la tabla 'resultados_academicos', reemplazando la original.
'''
import sqlite3
import pandas as pd

def actualizar_codigo_red():
    db_path = 'reasis_database.db'
    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)

    try:
        print("Cargando la tabla 'resultados_academicos'...")
        df = pd.read_sql_query("SELECT * FROM resultados_academicos", conn)

        print("Actualizando la columna 'codigo_red'...")
        # Asegurarse de que la columna region es de tipo string
        df['region'] = df['region'].astype(str)
        df['codigo_red'] = df['region'].str[:2]

        print("Mostrando una vista previa de los cambios:")
        print(df[['id', 'region', 'codigo_red']].head())

        # Guardar los cambios en la base de datos
        print("Guardando los cambios en la tabla 'resultados_academicos'...")
        df.to_sql('resultados_academicos', conn, if_exists='replace', index=False)
        print("La tabla ha sido actualizada exitosamente.")

    finally:
        conn.close()

if __name__ == "__main__":
    actualizar_codigo_red()
