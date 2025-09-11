# funciones/clustering/aplicar_x11_red_a_indices.py
import sqlite3, pandas as pd, glob, sys

def aplicar_x11(csv_path=None):
    if not csv_path:
        files = sorted(glob.glob('temp_data/x11_red_preliminar_*.csv'))
        if not files:
            print("No se encontró CSV preliminar en temp_data/.")
            return
        csv_path = files[-1]
    print(f"Usando CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    conn = sqlite3.connect('reasis_database.db')
    try:
        cur = conn.cursor()
        actualizadas = 0
        for _, r in df.iterrows():
            cur.execute(
                "UPDATE indices_metodologicos SET X11_RED = ? WHERE codigo_modular = ?",
                (float(r['X11_RED']), r['codigo_modular'])
            )
            actualizadas += cur.rowcount
        conn.commit()
        print(f"Filas actualizadas en indices_metodologicos: {actualizadas}")
    finally:
        conn.close()

if __name__ == '__main__':
    aplicar_x11(sys.argv[1] if len(sys.argv) > 1 else None)
