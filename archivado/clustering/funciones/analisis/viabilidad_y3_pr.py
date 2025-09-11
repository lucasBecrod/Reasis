import sqlite3
import pandas as pd


PREDICTORS_IDX = [
    'X11_RED', 'X13_TMATRC', 'X2_TR', 'X12_TOE', 'X1_NVC', 'X5_ED', 'X10_IE', 'X4_IDD', 'X6_CDD'
]

PREDICTORS_IE = [
    'area_censo', 'modalidad_especifica', 'nombre_red_fya_matched', 'numero_fya'
]


def main():
    conn = sqlite3.connect('reasis_database.db')
    try:
        total = pd.read_sql_query("SELECT COUNT(*) AS n FROM indices_metodologicos", conn).iloc[0]['n']
        print(f"Total instituciones en indices_metodologicos: {int(total)}")

        # Y1_ILA
        y1 = pd.read_sql_query(
            "SELECT SUM(CASE WHEN Y1_ILA IS NOT NULL THEN 1 ELSE 0 END) AS ok FROM indices_metodologicos",
            conn,
        ).iloc[0]['ok']
        print(f"Y1_ILA disponible: {int(y1)}/{int(total)} ({(y1/total*100):.1f}%)")

        # Predictores en indices_metodologicos
        for col in PREDICTORS_IDX:
            q = f"SELECT SUM(CASE WHEN {col} IS NOT NULL THEN 1 ELSE 0 END) AS ok FROM indices_metodologicos"
            try:
                n = pd.read_sql_query(q, conn).iloc[0]['ok']
                print(f"{col} disponible: {int(n)}/{int(total)} ({(n/total*100):.1f}%)")
            except Exception as e:
                print(f"{col} no existe: {e}")

        # Predictores del join con instituciones_educativas
        for col in PREDICTORS_IE:
            q = f"""
            SELECT SUM(CASE WHEN ie.{col} IS NOT NULL THEN 1 ELSE 0 END) AS ok
            FROM indices_metodologicos idx
            LEFT JOIN instituciones_educativas ie ON ie.codigo_modular = idx.CODIGO_MODULAR
            """
            try:
                n = pd.read_sql_query(q, conn).iloc[0]['ok']
                print(f"{col} (ie) disponible: {int(n)}/{int(total)} ({(n/total*100):.1f}%)")
            except Exception as e:
                print(f"{col} (ie) error: {e}")

    finally:
        conn.close()


if __name__ == '__main__':
    main()




