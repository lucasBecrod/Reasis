
'''
Script temporal para inspeccionar el esquema de la tabla 'indices_metodologicos'.
'''
import sqlite3

def inspect_indices_schema():
    db_path = 'reasis_database.db'
    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("\n--- Esquema de la tabla: indices_metodologicos ---")
        cursor.execute("PRAGMA table_info(indices_metodologicos)")
        schema = cursor.fetchall()
        if not schema:
            print("La tabla 'indices_metodologicos' no existe o está vacía.")
        else:
            for column in schema:
                print(column)

    finally:
        conn.close()

if __name__ == "__main__":
    inspect_indices_schema()

