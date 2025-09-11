import sqlite3
import pandas as pd
import json
import os
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

def completar_datos_excel():
    '''Completa los datos de las IIEE con información de un archivo Excel.'''
    db_path = 'reasis_database.db'
    excel_path = r"C:\Users\lucas\Proyectos\Reasis\assets\Consultoria\Información actualizada\1. Ruralidad, EIB y TOE.xlsx"
    sheet_name = 'DatosGlobales'
    json_path = 'lib/iiee_faltantes.json'

    mapeo_columnas = {
        'altitud': 'altitud',
        'd_forma': 'modalidad',
        'd_gestion': 'gestion',
        'd_ges_dep': 'gestion_departamental',
        'd_cod_tur': 'turno',
        'director': 'director',
        'telefono': 'telefono',
        'email': 'email',
        'dre_ugel': 'unidad_ejecutora',
        'NDirectivosH': 'directivos_hombres',
        'NDirectivosM': 'directivos_mujeres',
        'NDirectivosT': 'directivos_total',
        'NDocentesH': 'docentes_hombres',
        'NDocentesM': 'docentes_mujeres',
        'NDocentesT': 'docentes_total',
        'talumno': 'total_alumnos',
        'talum_hom': 'alumnos_hombres',
        'talum_muj': 'alumnos_mujeres'
    }

    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            iiee_faltantes_json = json.load(f)
        
        # Cargar datos del Excel
        print(f"Leyendo datos desde: {excel_path} | Hoja: {sheet_name}")
        df_excel = pd.read_excel(excel_path, sheet_name=sheet_name)
        df_excel['cod_mod'] = df_excel['cod_mod'].astype(str).str.zfill(7)
        df_excel['codlocal'] = df_excel['codlocal'].astype(str)

        # Obtener datos de las IIEE de la BD local para matching (nombre_institucion, codigo_local)
        df_instituciones_local = pd.read_sql_query("SELECT codigo_modular, nombre_institucion, codigo_local FROM instituciones_educativas", conn)

        update_count = 0
        for ie_json in iiee_faltantes_json:
            codigo_modular_json = ie_json['COD_MOD']
            codigo_local_json = str(ie_json.get('CODLOCAL', '')) # Asegurarse que sea string
            
            matched_excel_row = None

            # Estrategia 1: Match exacto por codigo_modular y codigo_local
            datos_excel_exact_match = df_excel[(df_excel['cod_mod'] == codigo_modular_json) & (df_excel['codlocal'] == codigo_local_json)]
            if not datos_excel_exact_match.empty:
                matched_excel_row = datos_excel_exact_match.iloc[0]
                print(f"MATCH exacto por codigo_modular y codigo_local para {codigo_modular_json} ({codigo_local_json})")
            else:
                # Si no hay match exacto, intentar otras estrategias
                ie_local_info = df_instituciones_local[df_instituciones_local['codigo_modular'] == codigo_modular_json]
                if not ie_local_info.empty:
                    nombre_local = ie_local_info.iloc[0]['nombre_institucion']
                    codigo_local_bd = ie_local_info.iloc[0]['codigo_local']

                    # Estrategia 2: Match por codigo_modular (solo) si no se encontró por cod_mod+codlocal
                    datos_excel_cod_mod = df_excel[df_excel['cod_mod'] == codigo_modular_json]
                    if not datos_excel_cod_mod.empty:
                        matched_excel_row = datos_excel_cod_mod.iloc[0]
                        print(f"MATCH por codigo_modular (solo) para {codigo_modular_json}")
                    else:
                        # Estrategia 3: Fuzzy match por nombre_institucion
                        if pd.notna(nombre_local):
                            best_match_name = process.extractOne(nombre_local, df_excel['cen_edu'].astype(str).tolist(), scorer=fuzz.token_sort_ratio)
                            if best_match_name and best_match_name[1] >= 85: # Umbral de confianza
                                matched_excel_row = df_excel[df_excel['cen_edu'].astype(str) == best_match_name[0]].iloc[0]
                                print(f"MATCH por nombre (fuzzy) para {codigo_modular_json} ({nombre_local}) con {best_match_name[0]} (Score: {best_match_name[1]}) ")

                        # Estrategia 4: Fuzzy match por codigo_local (si no se encontró por nombre)
                        if matched_excel_row is None and pd.notna(codigo_local_bd):
                            best_match_local = process.extractOne(codigo_local_bd, df_excel['codlocal'].astype(str).tolist(), scorer=fuzz.token_sort_ratio)
                            if best_match_local and best_match_local[1] >= 85: # Umbral de confianza
                                matched_excel_row = df_excel[df_excel['codlocal'].astype(str) == best_match_local[0]].iloc[0]
                                print(f"MATCH por codigo_local (fuzzy) para {codigo_modular_json} ({codigo_local_bd}) con {best_match_local[0]} (Score: {best_match_local[1]}) ")

            if matched_excel_row is None:
                print(f"ADVERTENCIA: No se encontraron datos en el Excel para {codigo_modular_json} usando ninguna estrategia. Se omite.")
                continue

            set_clauses = []
            params = []
            for origen, destino in mapeo_columnas.items():
                valor = matched_excel_row[origen]
                if pd.notna(valor):
                    set_clauses.append(f"{destino} = ?")
                    params.append(valor)
            
            # Manejo de es_rural y es_eib
            if 'ruralidad' in matched_excel_row and pd.notna(matched_excel_row['ruralidad']):
                set_clauses.append("es_rural = ?")
                params.append(1 if str(matched_excel_row['ruralidad']).strip().upper() == 'RURAL' else 0)
            if 'eib' in matched_excel_row and pd.notna(matched_excel_row['eib']):
                 set_clauses.append("es_eib = ?")
                 params.append(1 if str(matched_excel_row['eib']).strip().upper() != 'NO' else 0)

            if not set_clauses:
                continue

            params.append(codigo_modular_json)
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
    completar_datos_excel()
