import sqlite3
import pandas as pd
import re

def extract_digits(text):
    if pd.isna(text): return ''
    return ''.join(filter(str.isdigit, str(text)))

def update_clustering_flags():
    db_path = "reasis_database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    redes_clustering_numbers = ['44', '47', '48', '54', '72', '79']

    # Actualizar redes_fe_y_alegria
    df_redes = pd.read_sql_query("SELECT id, codigo_red FROM redes_fe_y_alegria", conn)
    
    for index, row in df_redes.iterrows():
        red_id = row['id']
        codigo_red = row['codigo_red']
        codigo_red_digits = extract_digits(codigo_red)
        
        if codigo_red_digits in redes_clustering_numbers:
            cursor.execute("UPDATE redes_fe_y_alegria SET entra_estudio_clustering = 'Sí' WHERE id = ?", (red_id,))
        else:
            cursor.execute("UPDATE redes_fe_y_alegria SET entra_estudio_clustering = 'No' WHERE id = ?", (red_id,))
    conn.commit()
    print("[OK] Column 'entra_estudio_clustering' in redes_fe_y_alegria updated.")

    # Actualizar instituciones_educativas
    cursor.execute("UPDATE instituciones_educativas SET entra_estudio_clustering = (SELECT r.entra_estudio_clustering FROM redes_fe_y_alegria r WHERE r.id = instituciones_educativas.id_red_fya) WHERE id_red_fya IS NOT NULL")
    cursor.execute("UPDATE instituciones_educativas SET entra_estudio_clustering = 'No' WHERE id_red_fya IS NULL OR entra_estudio_clustering IS NULL")
    conn.commit()
    print("[OK] Column 'entra_estudio_clustering' in instituciones_educativas updated.")

    conn.close()

if __name__ == "__main__":
    update_clustering_flags()
