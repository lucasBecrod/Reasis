import glob
import sqlite3
import pandas as pd
import sys


def asegurar_columnas(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(indices_metodologicos)")
    cols = [row[1] for row in cur.fetchall()]
    alter_ops = []
    if 'X13_TMATRC' not in cols:
        alter_ops.append("ALTER TABLE indices_metodologicos ADD COLUMN X13_TMATRC REAL")
    if 'X13_TMATRC_CATEGORIA' not in cols:
        alter_ops.append("ALTER TABLE indices_metodologicos ADD COLUMN X13_TMATRC_CATEGORIA TEXT")
    # Opcionales: almacenar métricas del test
    if 'X13_TMATRC_MANN_KENDALL_P' not in cols:
        alter_ops.append("ALTER TABLE indices_metodologicos ADD COLUMN X13_TMATRC_MANN_KENDALL_P REAL")
    for sql in alter_ops:
        cur.execute(sql)
    if alter_ops:
        conn.commit()


def aplicar(csv_path: str | None = None):
    if not csv_path:
        files = sorted(glob.glob('temp_data/x13_tmatrc_preliminar_*.csv'))
        if not files:
            print('No se encontró CSV preliminar en temp_data/.')
            return
        csv_path = files[-1]
    print(f'Usando CSV: {csv_path}')
    df = pd.read_csv(csv_path)

    conn = sqlite3.connect('reasis_database.db')
    try:
        asegurar_columnas(conn)
        cur = conn.cursor()
        actualizadas = 0
        for _, r in df.iterrows():
            cur.execute(
                'UPDATE indices_metodologicos SET X13_TMATRC = ?, X13_TMATRC_CATEGORIA = ?, X13_TMATRC_MANN_KENDALL_P = ? WHERE CODIGO_MODULAR = ?',
                (float(r['X13_TMATRC']), str(r.get('X13_TMATRC_CATEGORIA', '')), float(r.get('X13_TMATRC_MANN_KENDALL_P', None)) if pd.notna(r.get('X13_TMATRC_MANN_KENDALL_P', None)) else None, str(r['codigo_modular']))
            )
            actualizadas += cur.rowcount
        conn.commit()
        print(f'Filas actualizadas en indices_metodologicos: {actualizadas}')
    finally:
        conn.close()


if __name__ == '__main__':
    aplicar(sys.argv[1] if len(sys.argv) > 1 else None)


