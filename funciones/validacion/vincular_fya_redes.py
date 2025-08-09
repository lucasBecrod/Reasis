import pandas as pd
import sqlite3
from fuzzywuzzy import fuzz, process
import re

def extract_digits(text):
    if pd.isna(text): return ''
    return ''.join(filter(str.isdigit, str(text)))

def vincular_fya_redes():
    print("=== VINCULACIÓN DE IIEE A REDES FE Y ALEGRÍA ===")
    db_path = "reasis_database.db"
    conn = sqlite3.connect(db_path)

    try:
        # Cargar datos de instituciones_educativas
        df_iiee = pd.read_sql_query("SELECT * FROM instituciones_educativas", conn)
        # Cargar datos de redes_fe_y_alegria (ya normalizada)
        df_redes = pd.read_sql_query("SELECT * FROM redes_fe_y_alegria", conn)

        # Asegurarse de que las columnas de texto sean string para fuzzywuzzy
        df_iiee['numero_fya'] = df_iiee['numero_fya'].astype(str).fillna('')
        df_redes['codigo_red'] = df_redes['codigo_red'].astype(str).fillna('')
        df_redes['nombre_completo'] = df_redes['nombre_completo'].astype(str).fillna('')

        # Crear un mapeo de codigo_red (dígitos) a id para búsqueda directa
        codigo_red_digits_to_id = {extract_digits(row['codigo_red']): str(row['id']) for index, row in df_redes.iterrows()}
        
        # Crear un mapeo de nombre_completo a id para búsqueda
        nombre_completo_to_id = {row['nombre_completo']: str(row['id']) for index, row in df_redes.iterrows()}

        updates = []
        
        # Iterar sobre las IIEE que son de Fe y Alegría
        for index, row in df_iiee[df_iiee['es_fya'] == 1].iterrows():
            iiee_id = row['id']
            numero_fya_iiee = row['numero_fya']
            numero_fya_iiee_digits = extract_digits(numero_fya_iiee)
            
            matched_red_id = None
            matched_red_name = None

            if numero_fya_iiee_digits:
                # 1. Búsqueda directa por dígitos de codigo_red
                if numero_fya_iiee_digits in codigo_red_digits_to_id:
                    matched_red_id = codigo_red_digits_to_id[numero_fya_iiee_digits]
                    matched_red_name = df_redes[df_redes['id'] == int(matched_red_id)]['nombre_completo'].iloc[0]
                else:
                    # 2. Búsqueda por nombre completo (si el numero_fya_iiee es un nombre completo de red)
                    if numero_fya_iiee in nombre_completo_to_id:
                        matched_red_id = nombre_completo_to_id[numero_fya_iiee]
                        matched_red_name = numero_fya_iiee
                    else:
                        # 3. Fuzzy matching (como último recurso para encontrar una red existente)
                        redes_choices = df_redes['nombre_completo'].tolist() + df_redes['codigo_red'].tolist()
                        best_match = process.extractOne(numero_fya_iiee, redes_choices, scorer=fuzz.token_set_ratio)
                        SIMILARITY_THRESHOLD = 70
                        if best_match and best_match[1] >= SIMILARITY_THRESHOLD:
                            matched_red_name_candidate = best_match[0]
                            # Intentar obtener el ID por codigo_red o nombre_completo
                            if matched_red_name_candidate in nombre_completo_to_id:
                                matched_red_id = nombre_completo_to_id[matched_red_name_candidate]
                                matched_red_name = matched_red_name_candidate
                            elif matched_red_name_candidate in codigo_red_digits_to_id: # Si el match fue con un codigo_red
                                matched_red_id = codigo_red_digits_to_id[matched_red_name_candidate]
                                matched_red_name = df_redes[df_redes['id'] == int(matched_red_id)]['nombre_completo'].iloc[0]

                if matched_red_id:
                    updates.append({
                        'id': iiee_id,
                        'id_red_fya': int(matched_red_id),
                        'nombre_red_fya_matched': matched_red_name
                    })
        
        # Actualizar instituciones_educativas
        cursor = conn.cursor()
        for update_data in updates:
            cursor.execute("UPDATE instituciones_educativas SET id_red_fya = ?, nombre_red_fya_matched = ? WHERE id = ?",
                           (update_data['id_red_fya'], update_data['nombre_red_fya_matched'], update_data['id']))
        conn.commit()
        print(f"[OK] Se actualizaron {len(updates)} registros en instituciones_educativas.")

        print("\n[FIN] Proceso de vinculación completado.")

    except Exception as e:
        print(f"[ERROR] Ocurrió un error durante el proceso: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    vincular_fya_redes()