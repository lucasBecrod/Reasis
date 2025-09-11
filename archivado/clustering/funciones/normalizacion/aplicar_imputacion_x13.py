import glob
import sqlite3
import pandas as pd
import sys


def asegurar_columnas(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(indices_metodologicos)")
    cols = [row[1] for row in cur.fetchall()]
    if 'X13_TMATRC' not in cols:
        cur.execute("ALTER TABLE indices_metodologicos ADD COLUMN X13_TMATRC REAL")
    if 'X13_TMATRC_CATEGORIA' not in cols:
        cur.execute("ALTER TABLE indices_metodologicos ADD COLUMN X13_TMATRC_CATEGORIA TEXT")
    if 'X13_TMATRC_MANN_KENDALL_P' not in cols:
        cur.execute("ALTER TABLE indices_metodologicos ADD COLUMN X13_TMATRC_MANN_KENDALL_P REAL")
    conn.commit()


def aplicar(csv_path: str | None = None):
    if not csv_path:
        files = sorted(glob.glob('temp_data/x13_tmatrc_imputado_*.csv'))
        if not files:
            print('No se encontró CSV de imputación X13 en temp_data/.')
            return
        csv_path = files[-1]
    print(f'Usando CSV de imputación X13: {csv_path}')
    df = pd.read_csv(csv_path)

    conn = sqlite3.connect('reasis_database.db')
    try:
        asegurar_columnas(conn)
        cur = conn.cursor()
        actualizadas = 0
        for _, r in df.iterrows():
            cur.execute(
                'UPDATE indices_metodologicos SET X13_TMATRC = ? WHERE CODIGO_MODULAR = ?',
                (float(r['X13_TMATRC_imputado']), str(r['codigo_modular']))
            )
            actualizadas += cur.rowcount
        conn.commit()
        print(f'Filas actualizadas en indices_metodologicos: {actualizadas}')
    finally:
        conn.close()


if __name__ == '__main__':
    aplicar(sys.argv[1] if len(sys.argv) > 1 else None)




