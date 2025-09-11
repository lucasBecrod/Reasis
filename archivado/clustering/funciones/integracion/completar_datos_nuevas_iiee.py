import sqlite3
import pandas as pd
import json
import os
from simpledbf import Dbf5

def completar_datos_nuevas_iiee():
    '''Completa los datos de las nuevas IIEE con información del padrón nacional.'''
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
        'D_DREUGEL': 'unidad_ejecutora',
        'DAREACENSO': 'area_censo',
        'TALUMNO': 'total_alumnos',
        'TALUM_HOM': 'alumnos_hombres',
        'TALUM_MUJ': 'alumnos_mujeres',
        'TDOCENTE': 'total_docentes'
    }

    print(f"Conectando a base de datos: {db_path}")
    conn = sqlite3.connect(db_path)

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            iiee_faltantes = json.load(f)
        codigos_a_actualizar = [ie['COD_MOD'] for ie in iiee_faltantes]
        print(f"Se completarán los datos para {len(codigos_a_actualizar)} IIEE.")

        dbf = Dbf5(padron_path, codec='latin-1')
        df_padron = dbf.to_dataframe()
        df_padron['COD_MOD'] = df_padron['COD_MOD'].astype(str)

        update_count = 0
        for codigo in codigos_a_actualizar:
            datos_padron = df_padron[df_padron['COD_MOD'] == codigo]
            if datos_padron.empty:
                print(f"ADVERTENCIA: No se encontraron datos en el padrón para {codigo}. Se omite.")
                continue

            set_clauses = []
            params = []
            for origen, destino in mapeo_columnas.items():
                valor = datos_padron.iloc[0][origen]
                if pd.notna(valor):
                    set_clauses.append(f"{destino} = ?")
                    params.append(valor)
            
            # Derivar es_rural
            area_censo = datos_padron.iloc[0]['DAREACENSO']
            if pd.notna(area_censo):
                es_rural_valor = 1 if area_censo.strip().upper() == 'RURAL' else 0
                set_clauses.append("es_rural = ?")
                params.append(es_rural_valor)

            if not set_clauses:
                continue

            params.append(codigo)
            update_query = f"UPDATE instituciones_educativas SET {', '.join(set_clauses)} WHERE codigo_modular = ?"
            
            cursor = conn.cursor()
            cursor.execute(update_query, tuple(params))
            update_count += cursor.rowcount

        conn.commit()
        print(f"\nIntegración completada. Se actualizaron {update_count} registros.")

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    completar_datos_nuevas_iiee()
