import os
import json
from datetime import datetime
import sqlite3
import pandas as pd
import numpy as np
from math import erf, sqrt


YEARS = [2019, 2020, 2021, 2022, 2023, 2024]


def theil_sen_slope(xs: np.ndarray, ys: np.ndarray) -> float | None:
    # xs, ys deben ser arrays 1D del mismo tamaño (>= 2)
    n = len(xs)
    if n < 2:
        return None
    slopes = []
    for i in range(n - 1):
        for j in range(i + 1, n):
            dx = xs[j] - xs[i]
            if dx == 0:
                continue
            slopes.append((ys[j] - ys[i]) / dx)
    if not slopes:
        return None
    return float(np.median(slopes))


def mann_kendall_test(ys: np.ndarray) -> tuple[float, float, float]:
    # Retorna (S, Z, p_value) usando aproximación normal, ignorando corrección por empates
    n = len(ys)
    if n < 2:
        return 0.0, 0.0, 1.0
    S = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            diff = ys[j] - ys[i]
            sgn_pos = 1 if diff > 0 else 0
            sgn_neg = 1 if diff < 0 else 0
            S += (sgn_pos - sgn_neg)
    # Var(S) sin empates: n(n-1)(2n+5)/18
    varS = n * (n - 1) * (2 * n + 5) / 18.0
    if S > 0:
        Z = (S - 1) / sqrt(varS)
    elif S < 0:
        Z = (S + 1) / sqrt(varS)
    else:
        Z = 0.0
    # p-valor bilateral
    phi = lambda z: 0.5 * (1.0 + erf(z / sqrt(2)))
    p = 2.0 * (1.0 - phi(abs(Z)))
    return float(S), float(Z), float(p)


def categorizar_tendencia(slope: float, p_value: float) -> str:
    # Categorización robusta (umbral en estudiantes/año)
    if p_value < 0.05:
        if slope > 2:
            return 'CRECIMIENTO_SIGNIFICATIVO'
        if slope < -2:
            return 'DECRECIMIENTO_SIGNIFICATIVO'
        return 'CAMBIO_LEVE_SIGNIFICATIVO'
    return 'ESTABLE'


def calcular_x13_tmatrc():
    db_path = 'reasis_database.db'
    os.makedirs('temp_data', exist_ok=True)
    os.makedirs('data/intermedios', exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    print(f"Conectando a la base de datos: {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        # Cargar series de matrícula por institución
        cols = ', '.join([f"matric_siagie_{y}" for y in YEARS])
        q = f"""
        SELECT codigo_modular, nombre_institucion, {cols}
        FROM instituciones_educativas
        WHERE codigo_modular IS NOT NULL
        """
        df = pd.read_sql_query(q, conn)
        print(f"Instituciones cargadas: {len(df)}")

        resultados = []
        for _, r in df.iterrows():
            series = []
            years_used = []
            for y in YEARS:
                v = r.get(f'matric_siagie_{y}')
                if pd.notna(v):
                    years_used.append(y)
                    series.append(float(v))
            if len(series) < 4:
                continue  # criterio mínimo
            xs = np.array(years_used, dtype=float)
            ys = np.array(series, dtype=float)
            # Normalizar xs a años reales (no es necesario reindexar)
            slope = theil_sen_slope(xs, ys)
            if slope is None:
                continue
            # Mann-Kendall
            S, Z, p = mann_kendall_test(ys)
            categoria = categorizar_tendencia(slope, p)
            resultados.append({
                'codigo_modular': r['codigo_modular'],
                'nombre_institucion': r['nombre_institucion'],
                'X13_TMATRC': slope,
                'X13_TMATRC_MANN_KENDALL_S': S,
                'X13_TMATRC_MANN_KENDALL_Z': Z,
                'X13_TMATRC_MANN_KENDALL_P': p,
                'X13_TMATRC_CATEGORIA': categoria,
            })

        if not resultados:
            print('No se generaron resultados (verificar columnas de matrícula).')
            return

        df_out = pd.DataFrame(resultados)
        csv_path = f'temp_data/x13_tmatrc_preliminar_{ts}.csv'
        df_out.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"CSV generado: {csv_path} ({len(df_out)} filas)")

        # Resumen JSON
        resumen = {
            'timestamp': ts,
            'filas': int(len(df_out)),
            'estadisticas_slope': {
                'media': float(df_out['X13_TMATRC'].mean()),
                'mediana': float(df_out['X13_TMATRC'].median()),
                'min': float(df_out['X13_TMATRC'].min()),
                'max': float(df_out['X13_TMATRC'].max()),
                'p10': float(df_out['X13_TMATRC'].quantile(0.10)),
                'p90': float(df_out['X13_TMATRC'].quantile(0.90)),
            },
            'categorias': df_out['X13_TMATRC_CATEGORIA'].value_counts().to_dict(),
            'criterio_minimo_anos': 4,
            'metodo': 'Theil-Sen + Mann-Kendall (p<0.05) con umbrales ±2 ests/año',
            'origen': 'instituciones_educativas.matric_siagie_2019..2024',
            'destino': 'indices_metodologicos.X13_TMATRC / X13_TMATRC_CATEGORIA (pendiente aprobación)'
        }
        json_path = f'data/intermedios/x13_tmatrc_resumen_{ts}.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(resumen, f, ensure_ascii=False, indent=2)
        print(f"JSON resumen: {json_path}")

        # Muestra
        print(df_out.sample(n=min(5, len(df_out)), random_state=42).to_string(index=False))

    finally:
        conn.close()


if __name__ == '__main__':
    calcular_x13_tmatrc()


