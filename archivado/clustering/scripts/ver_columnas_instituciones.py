import sqlite3

DB_PATH = 'reasis_database.db'

def mostrar_columnas(tabla):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({tabla});")
    columnas = [col[1] for col in cur.fetchall()]
    print("Columnas de la tabla", tabla)
    for col in columnas:
        print(col)
    conn.close()

if __name__ == "__main__":
    mostrar_columnas('instituciones_educativas')