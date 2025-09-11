import sqlite3

DB_PATH = "reasis_database.db"

def mostrar_campos():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(instituciones_educativas);")
    for col in cur.fetchall():
        print(col)
    conn.close()

if __name__ == "__main__":
    mostrar_campos()