# funciones/clustering/calcular_y2_td.py
import sqlite3
import pandas as pd
import numpy as np

def calcular_y2_td():
    db_path = 'reasis_database.db'
    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        q = """
        SELECT codigo_modular, ILA_2022, ILA_2023, ILA_2024
        FROM instituciones_educativas
        WHERE codigo_modular IS NOT NULL
        """
        df = pd.read_sql_query(q, conn)
        resultados = []

        for _, r in df.iterrows():
            xs, ys = [], []
            for year in (2022, 2023, 2024):
                v = r.get(f'ILA_{year}')
                if pd.notna(v):
                    xs.append(year)
                    ys.append(float(v))
            if len(xs) >= 2:
                xs = np.array(xs, dtype=float)
                ys = np.array(ys, dtype=float)
                xs = xs - xs.min()  # normaliza a 0,1,2 para que la pendiente sea por año
                slope = float(np.polyfit(xs, ys, 1)[0])
                resultados.append((r['codigo_modular'], slope))

        cur = conn.cursor()
        actualizadas = 0
        for cod, td in resultados:
            cur.execute("UPDATE indices_metodologicos SET Y2_TD = ? WHERE codigo_modular = ?", (td, cod))
            actualizadas += cur.rowcount
        conn.commit()

        print(f"Y2_TD calculado para {len(resultados)} instituciones. Filas actualizadas: {actualizadas}")
        if resultados:
            m = pd.DataFrame(resultados, columns=['codigo_modular','Y2_TD']).sample(n=min(5, len(resultados)), random_state=42)
            print(m)
    finally:
        conn.close()

if __name__ == "__main__":
    calcular_y2_td()