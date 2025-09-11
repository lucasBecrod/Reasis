
'''
Script temporal para inspeccionar el esquema de la tabla 'resultados_academicos'.
'''
import sqlite3

def inspect_resultados_schema():
    db_path = 'reasis_database.db'
    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("\n--- Esquema de la tabla: resultados_academicos ---")
        cursor.execute("PRAGMA table_info(resultados_academicos)")
        schema = cursor.fetchall()
        for column in schema:
            print(column)

    finally:
        conn.close()

if __name__ == "__main__":
    inspect_resultados_schema()

