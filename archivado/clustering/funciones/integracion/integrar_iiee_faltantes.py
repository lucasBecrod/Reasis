'''
Script para identificar instituciones educativas (IIEE) faltantes en la base de datos local
y generar un archivo JSON con los datos obtenidos del padrón nacional.

Este script realiza las siguientes acciones:
1. Se conecta a la base de datos SQLite 'reasis_database.db'.
2. Obtiene la lista de códigos modulares de la tabla 'resultados_academicos'.
3. Obtiene la lista de códigos modulares de la tabla 'instituciones_educativas'.
4. Identifica los códigos modulares que están en 'resultados_academicos' pero no en 'instituciones_educativas'.
5. Lee el archivo DBF 'Padron_web.dbf' del padrón nacional de IIEE.
6. Busca los datos de las IIEE faltantes en el padrón nacional.
7. Crea un directorio 'lib' si no existe.
8. Guarda los datos de las IIEE faltantes en un archivo JSON llamado 'lib/iiee_faltantes.json'.
'''
import sqlite3
import json
import os
from simpledbf import Dbf5

def identificar_iiee_faltantes():
    db_path = 'reasis_database.db'
    padron_path = 'data/bases_de_datos/Padron_web_20250731/Padron_web.dbf'
    output_dir = 'lib'
    output_path = os.path.join(output_dir, 'iiee_faltantes.json')

    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Obteniendo códigos modulares de 'resultados_academicos'...")
        cursor.execute("SELECT DISTINCT codigo_modular FROM resultados_academicos")
        codigos_resultados = {row[0] for row in cursor.fetchall()}
        print(f"Se encontraron {len(codigos_resultados)} códigos modulares únicos.")

        print("Obteniendo códigos modulares de 'instituciones_educativas'...")
        cursor.execute("SELECT DISTINCT codigo_modular FROM instituciones_educativas")
        codigos_instituciones = {row[0] for row in cursor.fetchall()}
        print(f"Se encontraron {len(codigos_instituciones)} códigos modulares únicos.")

    finally:
        conn.close()

    codigos_faltantes = codigos_resultados - codigos_instituciones
    print(f"Se identificaron {len(codigos_faltantes)} IIEE faltantes.")

    if not codigos_faltantes:
        print("No hay IIEE faltantes que procesar.")
        return

    print(f"Leyendo el padrón nacional de IIEE desde: {padron_path}")
    try:
        dbf = Dbf5(padron_path, codec='latin-1')
        df_padron = dbf.to_dataframe()
    except Exception as e:
        print(f"Error al leer el archivo DBF: {e}")
        return

    # Convertir la columna de código modular a string para la comparación
    df_padron['COD_MOD'] = df_padron['COD_MOD'].astype(str)
    codigos_faltantes_str = {str(c) for c in codigos_faltantes}

    print("Buscando IIEE faltantes en el padrón...")
    iiee_faltantes_data = df_padron[df_padron['COD_MOD'].isin(codigos_faltantes_str)]

    print(f"Se encontraron {len(iiee_faltantes_data)} de las {len(codigos_faltantes)} IIEE faltantes en el padrón.")

    if not os.path.exists(output_dir):
        print(f"Creando el directorio: {output_dir}")
        os.makedirs(output_dir)

    # Convertir el DataFrame a una lista de diccionarios para el JSON
    data_to_save = iiee_faltantes_data.to_dict(orient='records')

    print(f"Guardando los datos en: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, indent=4, ensure_ascii=False)

    print("Proceso completado exitosamente.")

if __name__ == "__main__":
    identificar_iiee_faltantes()
