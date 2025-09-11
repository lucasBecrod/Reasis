import sqlite3
import pandas as pd
import json
import os
from simpledbf import Dbf5

def validar_datos_nuevas_iiee():
    '''Valida los datos de las nuevas IIEE.'''
    db_path = 'reasis_database.db'
    padron_path = 'data/bases_de_datos/Padron_web_20250731/Padron_web.dbf'
    json_path = 'lib/iiee_faltantes.json'

    mapeo_columnas = {
        'D_NIV_MOD': 'nivel_educativo',
        'D_FORMA': 'modalidad',
        'D_GESTION': 'gestion',
        'D_GES_DEP': 'gestion_departamental',
        'D_COD_TUR': 'turno',
        'DIRECTOR': 'director',
        'TELEFONO': 'telefono',
        'EMAIL': 'email',
        'D_DPTO': 'departamento',
        'D_PROV': 'provincia',
        'D_DIST': 'distrito',
        'NLAT_IE': 'latitud',
        'NLONG_IE': 'longitud'
    }

    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            iiee_faltantes = json.load(f)
        codigos_nuevos = [ie['COD_MOD'] for ie in iiee_faltantes]
        
        muestra_codigos = codigos_nuevos[:4]
        print(f"Tomando una muestra de {len(muestra_codigos)} IIEE para validación: {muestra_codigos}")

        dbf = Dbf5(padron_path, codec='latin-1')
        df_padron = dbf.to_dataframe()
        df_padron['COD_MOD'] = df_padron['COD_MOD'].astype(str)

        for codigo in muestra_codigos:
            print(f"\n--- VALIDANDO CÓDIGO MODULAR: {codigo} ---")
            
            datos_padron = df_padron[df_padron['COD_MOD'] == codigo]
            if datos_padron.empty:
                print("No encontrado en el Padrón Nacional.")
                continue
            
            print("\n[DATOS DEL PADRÓN NACIONAL]")
            datos_padron_muestra = datos_padron[list(mapeo_columnas.keys())].iloc[0]
            print(datos_padron_muestra)

            query = f"SELECT {', '.join(mapeo_columnas.values())} FROM instituciones_educativas WHERE codigo_modular = ?"
            datos_locales = pd.read_sql_query(query, conn, params=(codigo,))
            print("\n[DATOS ACTUALES EN TU BASE DE DATOS]")
            if datos_locales.empty:
                print("No encontrado en la base de datos local.")
            else:
                print(datos_locales.iloc[0])

    except Exception as e:
        print(f"Ocurrió un error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    validar_datos_nuevas_iiee()
