import sqlite3
import pandas as pd

def investigate_unmatched():
    '''Investigates unmatched institutions.'''
    db_path = 'reasis_database.db'
    
    # List of unmatched codes from previous run
    unmatched_codes = [
        '0488403',
        '0481093', # Appears twice in the input list
        '0304642',
        '2533906',
        '1768829',
        '1781897'
    ]

    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)

    try:
        print("Retrieving details for unmatched institutions from 'instituciones_educativas'...")
        query = f"SELECT codigo_modular, nombre_institucion, codigo_local FROM instituciones_educativas WHERE codigo_modular IN ({','.join(['?' for _ in unmatched_codes])})"
        df_unmatched = pd.read_sql_query(query, conn, params=unmatched_codes)

        print("\n--- Details of Unmatched Institutions ---")
        print(df_unmatched)

    except Exception as e:
        print(f"Ocurrió un error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    investigate_unmatched()
