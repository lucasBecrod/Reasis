import sqlite3

DB_PATH = "reasis_database.db"

def poblar_codigo_rer():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Asignar código único según nombre_completo
    updates = [
        (48, "%Piura%"),
        (47, "%Loreto%"),
        (72, "%Ucayali%"),
        (44, "%Cusco%"),
        (54, "%Ancash%"),
        (79, "%Huancavelica%"),
    ]
    for codigo, patron in updates:
        cur.execute(
            "UPDATE redes_fe_y_alegria SET codigo_rer = ? WHERE nombre_completo LIKE ?;",
            (codigo, patron)
        )
    conn.commit()
    conn.close()
    print("Campo codigo_rer poblado en redes_fe_y_alegria.")

if __name__ == "__main__":
    poblar_codigo_rer()