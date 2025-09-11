import pandas as pd
import sqlite3
import re

def extract_core_red_number(nombre_completo):
    if pd.isna(nombre_completo): return None
    match = re.search(r'(?:Fe y Alegr[ií]a|FA)\s*(\d+)', str(nombre_completo), re.IGNORECASE)
    if match: return match.group(1)
    return None

def populate_normalized_fya_networks():
    print("=== PRE-POBLANDO REDES FE Y ALEGRÍA NORMALIZADAS ===")
    db_path = "reasis_database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Extraer números de RER únicos de instituciones_educativas.numero_fya
        df_iiee = pd.read_sql_query("SELECT DISTINCT numero_fya FROM instituciones_educativas WHERE es_fya = 1", conn)
        
        unique_red_numbers = set()
        for num_fya in df_iiee['numero_fya']:
            core_number = extract_core_red_number(num_fya)
            if core_number: unique_red_numbers.add(core_number)
        
        print(f"[INFO] Se encontraron {len(unique_red_numbers)} números de red Fe y Alegría únicos en instituciones_educativas.")

        # 2. Limpiar la tabla redes_fe_y_alegria
        cursor.execute("DELETE FROM redes_fe_y_alegria")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='redes_fe_y_alegria'") # Reset auto-increment ID
        conn.commit()
        print("[INFO] Tabla redes_fe_y_alegria limpiada.")

        # 3. Insertar los números únicos como nuevas redes
        new_redes_data = []
        for i, red_number in enumerate(sorted(list(unique_red_numbers))):
            new_redes_data.append({
                'id': i + 1, # Asignar ID secuencial
                'codigo_red': red_number,
                'nombre_completo': f"Red Fe y Alegría {red_number}",
                'numero_region': '', 'lugar': '', 'ambito': '', 'red_lugar': '',
                'entra_estudio_clustering': 'No' # Por defecto, se actualizará después
            })
        
        if new_redes_data:
            df_new_redes = pd.DataFrame(new_redes_data)
            df_new_redes.to_sql('redes_fe_y_alegria', conn, if_exists='append', index=False)
            conn.commit()
            print(f"[OK] Se insertaron {len(new_redes_data)} redes Fe y Alegría normalizadas.")

        print("\n[FIN] Pre-población de redes Fe y Alegría completada.")

    except Exception as e:
        print(f"[ERROR] Ocurrió un error durante el proceso: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    populate_normalized_fya_networks()
