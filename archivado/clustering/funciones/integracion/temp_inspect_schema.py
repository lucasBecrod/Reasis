
'''
Script temporal para inspeccionar el esquema de las tablas
'instituciones_educativas' y 'redes_fe_y_alegria' en la base de datos.
'''
import sqlite3

def inspect_schema():
    db_path = 'reasis_database.db'
    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("\n--- Esquema de la tabla: instituciones_educativas ---")
        cursor.execute("PRAGMA table_info(instituciones_educativas)")
        schema_ie = cursor.fetchall()
        for column in schema_ie:
            print(column)

        print("\n--- Esquema de la tabla: redes_fe_y_alegria ---")
        cursor.execute("PRAGMA table_info(redes_fe_y_alegria)")
        schema_redes = cursor.fetchall()
        for column in schema_redes:
            print(column)

    finally:
        conn.close()

if __name__ == "__main__":
    inspect_schema()

