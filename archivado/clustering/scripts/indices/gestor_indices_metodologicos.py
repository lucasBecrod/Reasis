import sqlite3
import pandas as pd
import os
from datetime import datetime

DB_PATH = 'reasis_database.db'
BACKUP_DIR = 'data/backups'

def backup_tabla_a_csv(db_path, table_name, backup_dir):
    """
    Respalda una tabla de la base de datos a un archivo CSV.
    """
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"Directorio de backups creado en: {backup_dir}")

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"{table_name}_backup_{fecha}.csv")
        df.to_csv(backup_path, index=False, encoding="utf-8")
        print(f"Backup de {table_name} guardado en: {backup_path}")
    except Exception as e:
        print(f"Error al respaldar la tabla: {e}")
    finally:
        conn.close()

def recrear_tabla_indices(db_path):
    """
    Elimina la tabla 'indices_metodologicos' existente y la crea con la nueva estructura alineada a la matriz de operacionalización,
    usando nombres de columnas en MAYÚSCULA.
    """
    sql_drop = "DROP TABLE IF EXISTS indices_metodologicos;"
    sql_create = """
    CREATE TABLE indices_metodologicos (
        -- Identificación y georreferencia
        CODIGO_MODULAR TEXT PRIMARY KEY,
        NOMBRE_INSTITUCION TEXT,
        NUMERO_FYA INTEGER,
        LATITUD REAL,
        LONGITUD REAL,
        ALTITUD_MSNM REAL,

        -- === VARIABLES DEPENDIENTES (Y) ===
        Y1_ILA REAL,
        Y2_TD REAL,
        Y3_PR REAL,

        -- === VARIABLES INDEPENDIENTES (X) - CONTEXTO ===
        X1_NVC REAL,
        X2_TR INTEGER,

        -- === VARIABLES INDEPENDIENTES (X) - DOCENTE ===
        X4_IDD REAL,
        X5_ED REAL,
        X6_CDD REAL,

        -- === VARIABLES INDEPENDIENTES (X) - RECURSOS ===
        X10_IE REAL,
        X11_RED REAL,
        X12_TOE INTEGER,

        -- === VARIABLES INDEPENDIENTES (X) - ESTUDIANTES/FAMILIAS ===
        X15_MEIB INTEGER,

        -- === VARIABLES ESTANDARIZADAS (Z-SCORE) PARA CLUSTERING ===
        Y1_ILA_ZSCORE REAL,
        Y2_TD_ZSCORE REAL,
        Y3_PR_ZSCORE REAL,
        X1_NVC_ZSCORE REAL,
        X4_IDD_ZSCORE REAL,
        X5_ED_ZSCORE REAL,
        X6_CDD_ZSCORE REAL,
        X10_IE_ZSCORE REAL,
        X11_RED_ZSCORE REAL,

        -- Auditoría
        FECHA_CALCULO TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(sql_drop)
        cur.execute(sql_create)
        conn.commit()
        print("Tabla 'indices_metodologicos' recreada con nombres de columnas en MAYÚSCULA.")

def poblar_indices_metodologicos(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            codigo_modular,
            nombre_institucion,
            numero_fya,
            latitud,
            longitud,
            altitud,
            ILA_2022,
            ILA_2023,
            ILA_2024,
            X11_RED,
            X11_RED_ajustado
        FROM instituciones_educativas
        WHERE entra_estudio_clustering = 'Sí'
    """)
    rows = cur.fetchall()

    for row in rows:
        (
            CODIGO_MODULAR, NOMBRE_INSTITUCION, NUMERO_FYA, LATITUD, LONGITUD, ALTITUD_MSNM,
            ILA_2022, ILA_2023, ILA_2024, X11_RED, X11_RED_ZSCORE
        ) = row

        # Y1_ILA: último año disponible
        Y1_ILA = ILA_2024 if ILA_2024 is not None else (ILA_2023 if ILA_2023 is not None else ILA_2022)
        # Y2_TD: tendencia
        Y2_TD = None
        if ILA_2022 is not None and ILA_2024 is not None and ILA_2022 != 0:
            Y2_TD = (ILA_2024 - ILA_2022) / ILA_2022

        cur.execute("""
            INSERT OR REPLACE INTO indices_metodologicos (
                CODIGO_MODULAR, NOMBRE_INSTITUCION, NUMERO_FYA, LATITUD, LONGITUD, ALTITUD_MSNM,
                Y1_ILA, Y2_TD, X11_RED, X11_RED_ZSCORE
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            CODIGO_MODULAR, NOMBRE_INSTITUCION, NUMERO_FYA, LATITUD, LONGITUD, ALTITUD_MSNM,
            Y1_ILA, Y2_TD, X11_RED, X11_RED_ZSCORE
        ))

    conn.commit()
    conn.close()
    print("Tabla 'indices_metodologicos' poblada con datos disponibles y encabezados en mayúsculas.")

if __name__ == "__main__":
    backup_tabla_a_csv(DB_PATH, 'indices_metodologicos', BACKUP_DIR)
    recrear_tabla_indices(DB_PATH)
    poblar_indices_metodologicos(DB_PATH)

