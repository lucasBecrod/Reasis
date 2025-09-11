import sqlite3
import pandas as pd
import numpy as np


YEARS = [2019, 2020, 2021, 2022, 2023, 2024]


def main():
    conn = sqlite3.connect('reasis_database.db')
    try:
        # Obtener faltantes en indices
        df_missing = pd.read_sql_query(
            "SELECT CODIGO_MODULAR FROM indices_metodologicos WHERE X13_TMATRC IS NULL",
            conn
        )
        if df_missing.empty:
            print('No hay faltantes de X13_TMATRC para completar.')
            return

        # Mediana global existente
        df_med = pd.read_sql_query(
            "SELECT X13_TMATRC FROM indices_metodologicos WHERE X13_TMATRC IS NOT NULL",
            conn
        )
        mediana_global = float(df_med['X13_TMATRC'].median()) if not df_med.empty else 0.0
        print(f"Mediana global existente X13_TMATRC: {mediana_global:.3f}")

        actualizadas = 0
        cur = conn.cursor()

        for _, row in df_missing.iterrows():
            cod = str(row['CODIGO_MODULAR'])
            cols = ', '.join([f"matric_siagie_{y}" for y in YEARS])
            q = f"""
                SELECT {cols} FROM instituciones_educativas WHERE codigo_modular = ?
            """
            df_ie = pd.read_sql_query(q, conn, params=[cod])
            if df_ie.empty:
                # No hay registro en IE; usar mediana global
                slope = mediana_global
                categoria = 'ESTABLE'
            else:
                values = []
                years = []
                for y in YEARS:
                    v = df_ie.at[0, f'matric_siagie_{y}']
                    if pd.notna(v):
                        years.append(y)
                        values.append(float(v))
                if len(values) >= 2:
                    xs = np.array(years, dtype=float)
                    ys = np.array(values, dtype=float)
                    slope = float(np.polyfit(xs, ys, 1)[0])
                    categoria = 'ESTABLE' if abs(slope) <= 2 else 'CAMBIO_LEVE_SIGNIFICATIVO'
                else:
                    slope = mediana_global
                    categoria = 'ESTABLE'

            cur.execute(
                "UPDATE indices_metodologicos SET X13_TMATRC = ?, X13_TMATRC_CATEGORIA = ? WHERE CODIGO_MODULAR = ?",
                (slope, categoria, cod)
            )
            actualizadas += cur.rowcount

        conn.commit()
        print(f"Filas actualizadas (fallbacks): {actualizadas}")

    finally:
        conn.close()


if __name__ == '__main__':
    main()




