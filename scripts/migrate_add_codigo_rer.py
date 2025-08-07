import sqlite3

DB_PATH = "reasis_database.db"

def add_codigo_rer():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Agregar campo a redes_fe_y_alegria si no existe
    try:
        cur.execute("ALTER TABLE redes_fe_y_alegria ADD COLUMN codigo_rer INTEGER;")
        print("Campo codigo_rer agregado a redes_fe_y_alegria.")
    except sqlite3.OperationalError:
        print("Campo codigo_rer ya existe en redes_fe_y_alegria.")

    # Agregar campo a instituciones_educativas si no existe
    try:
        cur.execute("ALTER TABLE instituciones_educativas ADD COLUMN codigo_rer INTEGER;")
        print("Campo codigo_rer agregado a instituciones_educativas.")
    except sqlite3.OperationalError:
        print("Campo codigo_rer ya existe en instituciones_educativas.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_codigo_rer()