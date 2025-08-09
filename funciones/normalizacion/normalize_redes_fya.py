import pandas as pd
import sqlite3
import re

def extract_core_red_number(nombre_completo):
    if pd.isna(nombre_completo): return None
    match = re.search(r'(?:Fe y Alegr[ií]a|FA)\s*(\d+)', str(nombre_completo), re.IGNORECASE)
    if match: return match.group(1)
    return None

def normalize_redes_fya():
    print("=== NORMALIZACIÓN DE REDES FE Y ALEGRÍA ===")
    db_path = "reasis_database.db"
    conn = sqlite3.connect(db_path)

    try:
        # 1. Cargar datos
        df_redes = pd.read_sql_query("SELECT * FROM redes_fe_y_alegria", conn)
        df_iiee = pd.read_sql_query("SELECT * FROM instituciones_educativas", conn)

        # 2. Generar new_codigo_red
        df_redes['new_codigo_red'] = df_redes['nombre_completo'].apply(extract_core_red_number)

        # 3. Identificar maestros y duplicados
        master_ids = {}
        id_to_master_id_map = {}
        ids_to_delete = set()

        for new_code, group in df_redes.groupby('new_codigo_red'):
            if new_code is None: 
                continue
            
            master_id = group['id'].min()
            master_ids[new_code] = master_id
            
            for original_id in group['id']:
                if original_id != master_id:
                    id_to_master_id_map[original_id] = master_id
                    ids_to_delete.add(original_id)
        
        print(f"[INFO] Se identificaron {len(ids_to_delete)} redes duplicadas para consolidar.")

        # 4. Actualizar instituciones_educativas usando una tabla temporal
        if id_to_master_id_map:
            df_id_map = pd.DataFrame(list(id_to_master_id_map.items()), columns=['original_id', 'master_id'])
            df_id_map.to_sql('redes_fya_id_map_temp', conn, if_exists='replace', index=False)
            
            cursor = conn.cursor()
            cursor.execute("UPDATE instituciones_educativas SET id_red_fya = (SELECT master_id FROM redes_fya_id_map_temp WHERE original_id = instituciones_educativas.id_red_fya) WHERE id_red_fya IN (SELECT original_id FROM redes_fya_id_map_temp)")
            updated_iiee_count = cursor.rowcount
            conn.commit()
            print(f"[INFO] Se actualizaron {updated_iiee_count} referencias en instituciones_educativas.")
            
            cursor.execute("DROP TABLE redes_fya_id_map_temp;")
        else:
            print("[INFO] No hay referencias de IIEE para actualizar.")

        # 5. Actualizar y eliminar en redes_fe_y_alegria
        cursor = conn.cursor()
        # Actualizar codigo_red de las filas maestras
        for new_code, master_id in master_ids.items():
            cursor.execute("UPDATE redes_fe_y_alegria SET codigo_red = ? WHERE id = ?", (new_code, master_id))
        conn.commit()
        print("[INFO] Se actualizaron los codigo_red de las redes maestras.")

        # Eliminar las filas duplicadas
        if ids_to_delete:
            placeholders = ', '.join(['?' for _ in ids_to_delete])
            cursor.execute(f"DELETE FROM redes_fe_y_alegria WHERE id IN ({placeholders})", tuple(ids_to_delete))
            conn.commit()
            print(f"[INFO] Se eliminaron {len(ids_to_delete)} redes duplicadas.")
        else:
            print("[INFO] No se encontraron redes duplicadas para eliminar.")

        print("\n[FIN] Normalización de redes Fe y Alegría completada.")

    except Exception as e:
        print(f"[ERROR] Ocurrió un error durante el proceso: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    normalize_redes_fya()