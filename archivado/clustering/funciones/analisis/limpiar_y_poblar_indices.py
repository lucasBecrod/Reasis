
'''
Script para limpiar y repoblar la tabla 'indices_metodologicos'.

Acciones:
1. Borra todos los datos existentes en 'indices_metodologicos'.
2. Selecciona la información básica de las IIEE desde 'instituciones_educativas'.
3. Inserta estos datos en 'indices_metodologicos', dejando los campos de índices vacíos (NULL).
'''
import sqlite3
import pandas as pd

def limpiar_y_poblar_indices():
    db_path = 'reasis_database.db'
    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Paso 1: Limpiar la tabla
        print("Borrando todos los datos de la tabla 'indices_metodologicos'...")
        cursor.execute("DELETE FROM indices_metodologicos")
        print(f"{cursor.rowcount} filas fueron eliminadas.")

        # Paso 2: Obtener los datos base de instituciones_educativas
        print("Obteniendo datos base de 'instituciones_educativas'...")
        df_instituciones = pd.read_sql_query("SELECT codigo_modular, nombre_institucion, numero_fya, nombre_red_fya_matched FROM instituciones_educativas", conn)
        print(f"Se obtuvieron {len(df_instituciones)} registros.")

        

        # Paso 3: Insertar los nuevos datos
        print("Insertando datos en 'indices_metodologicos'...")
        # Usamos to_sql para insertar el dataframe. Las columnas que no están en el df, quedarán como NULL
        df_instituciones.to_sql('indices_metodologicos', conn, if_exists='append', index=False)
        print("La tabla ha sido repoblada exitosamente.")

        # Verificación (opcional)
        print("\nVerificando los primeros 5 registros insertados:")
        df_verificacion = pd.read_sql_query("SELECT * FROM indices_metodologicos LIMIT 5", conn)
        print(df_verificacion)

        conn.commit()

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    limpiar_y_poblar_indices()
