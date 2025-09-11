'''
Script para generar un archivo JSON con información de una IIEE específica
que no fue encontrada en el padrón nacional, para su identificación manual.
'''
import sqlite3
import json
import pandas as pd
import os

def generar_json_ie_no_encontrada():
    db_path = 'reasis_database.db'
    codigo_modular_buscado = '658427'
    output_dir = 'lib'
    output_path = os.path.join(output_dir, f'iiee_no_encontrada_{codigo_modular_buscado}.json')

    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)

    try:
        print(f"Buscando datos para el código modular: {codigo_modular_buscado} en la tabla 'resultados_academicos'...")
        # Usamos pandas para facilitar la conversión a diccionario
        df = pd.read_sql_query(f"SELECT * FROM resultados_academicos WHERE codigo_modular = ?", conn, params=(codigo_modular_buscado,))

        if df.empty:
            print(f"No se encontró ninguna entrada para el código modular {codigo_modular_buscado}")
            return

        # Tomamos el primer registro si hay múltiples
        datos_ie = df.iloc[0].to_dict()

        # Eliminar campos que podrían no ser útiles para la identificación manual
        # y asegurarse de que todos los valores son serializables
        datos_limpios = {}
        for key, value in datos_ie.items():
            # Pandas puede devolver tipos de numpy que no son serializables por defecto en JSON
            if pd.isna(value):
                datos_limpios[key] = None
            elif hasattr(value, 'item'): # Convertir tipos de numpy a tipos nativos de Python
                datos_limpios[key] = value.item()
            else:
                datos_limpios[key] = value

        print("Datos encontrados:")
        print(datos_limpios)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"Creando archivo JSON en: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(datos_limpios, f, indent=4, ensure_ascii=False)

        print("Archivo JSON creado exitosamente.")

    finally:
        conn.close()

if __name__ == "__main__":
    generar_json_ie_no_encontrada()
