import glob
import sqlite3
import pandas as pd
import sys


def aplicar(csv_path: str | None = None):
    if not csv_path:
        files = sorted(glob.glob('temp_data/x11_red_imputado_*.csv'))
        if not files:
            print('No se encontró CSV de imputación en temp_data/.')
            return
        csv_path = files[-1]

    print(f'Usando CSV de imputación: {csv_path}')
    df = pd.read_csv(csv_path)

    conn = sqlite3.connect('reasis_database.db')
    try:
        cur = conn.cursor()
        actualizadas = 0
        for _, r in df.iterrows():
            if pd.notna(r['X11_RED_imputado']):
                cur.execute(
                    'UPDATE indices_metodologicos SET X11_RED = ? WHERE CODIGO_MODULAR = ?',
                    (float(r['X11_RED_imputado']), str(r['codigo_modular']))
                )
                actualizadas += cur.rowcount
        conn.commit()
        print(f'Filas actualizadas en indices_metodologicos: {actualizadas}')
    finally:
        conn.close()


if __name__ == '__main__':
    aplicar(sys.argv[1] if len(sys.argv) > 1 else None)


