import sqlite3, pandas as pd, numpy as np, os, json
from datetime import datetime

def calcular_x11_red():
    db_path = 'reasis_database.db'
    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs('temp_data', exist_ok=True)
    os.makedirs('data/intermedios', exist_ok=True)
    try:
        q = """
        SELECT codigo_modular, nombre_institucion, total_alumnos, total_docentes
        FROM instituciones_educativas
        WHERE codigo_modular IS NOT NULL
        """
        df = pd.read_sql_query(q, conn)

        df_valid = df[
            df['total_alumnos'].notna() & df['total_docentes'].notna() &
            (df['total_alumnos'] > 0) & (df['total_docentes'] > 0)
        ].copy()

        if df_valid.empty:
            print("No hay filas válidas para calcular X11_RED.")
            return

        df_valid['X11_RED'] = df_valid['total_alumnos'] / df_valid['total_docentes']

        csv_path = f'temp_data/x11_red_preliminar_{ts}.csv'
        df_valid[['codigo_modular','nombre_institucion','total_alumnos','total_docentes','X11_RED']].to_csv(csv_path, index=False, encoding='utf-8')
        print(f"CSV generado: {csv_path} ({len(df_valid)} filas)")

        # Resumen JSON
        x = df_valid['X11_RED']
        resumen = {
            'timestamp': ts,
            'filas_validas': int(len(df_valid)),
            'estadisticas': {
                'media': float(x.mean()), 'mediana': float(x.median()),
                'min': float(x.min()), 'max': float(x.max()),
                'p10': float(x.quantile(0.10)), 'p25': float(x.quantile(0.25)),
                'p75': float(x.quantile(0.75)), 'p90': float(x.quantile(0.90))
            },
            'reglas': 'X11_RED = total_alumnos / total_docentes; solo >0 y no nulos',
            'origen_tabla': 'instituciones_educativas',
            'destino_final': 'indices_metodologicos.X11_RED (pendiente aprobación)'
        }
        json_path = f'data/intermedios/x11_red_resumen_{ts}.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(resumen, f, ensure_ascii=False, indent=2)
        print(f"JSON resumen: {json_path}")

        # Muestra
        print(df_valid[['codigo_modular','nombre_institucion','X11_RED']].sample(n=min(5,len(df_valid)), random_state=42))
    finally:
        conn.close()

if __name__ == "__main__":
    calcular_x11_red()
