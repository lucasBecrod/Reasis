#!/usr/bin/env python3
"""
Generador de snapshot de Z-Scores (avanzado) desde indices_metodologicos.

Salida: Tabla materializada `indices_zscores_avanzado` con columnas:
- CODIGO_MODULAR
- <columna>_ZS para cada variable numérica seleccionada

Notas:
- No modifica `indices_metodologicos`
- Ignora valores NULL al calcular media/desviación (pandas default)
- Si desviación es 0 o ~0, deja ZSCORE como 0 para valores presentes (o NaN si prefieres)
"""

from __future__ import annotations

import sqlite3
from typing import List

import numpy as np
import pandas as pd


DATABASE_PATH = "reasis_database.db"


def columnas_objetivo(conn: sqlite3.Connection) -> List[str]:
    """Detecta columnas candidatas (metodológicas + contextuales) existentes."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(indices_metodologicos)")
    cols = {row[1] for row in cursor.fetchall()}

    base_met = [
        "Y1_ILA", "Y2_TD", "Y3_PR",
        "X1_NVC", "X2_TR", "X4_IDD", "X6_CDD", "X10_IE",
        "X11_RED", "X11_RED_ajustado", "X12_TOE", "X13_TMATRC",
    ]
    base_ctx = [
        "X14_NIVEL_EDUCATIVO", "X16_MODALIDAD", "X17_GESTION", "X18_TURNO",
        "X19_ORGANIZACION_PEDAGOGICA", "X20_DIRECTIVOS_TOTAL", "X21_MULTIPLICIDAD1",
        "X22_MULTIPLICIDAD2", "X23_POBREZA_DISTRITO", "X24_GPMD", "X25_POBLACION_DISTRITO",
    ]

    candidatos = [c for c in base_met + base_ctx if c in cols]
    # preferir X11_RED_ajustado si existe
    if "X11_RED_ajustado" in candidatos and "X11_RED" in candidatos:
        candidatos.remove("X11_RED")
    return candidatos


def calcular_zscores(df: pd.DataFrame, columnas: List[str]) -> pd.DataFrame:
    """Devuelve DataFrame con columnas *_ZS calculadas.

    Z = (x - media)/std usando ddof=0 y NaN-safe. std ~0 => z=0 para valores presentes.
    """
    z = pd.DataFrame(index=df.index)
    for col in columnas:
        serie = pd.to_numeric(df[col], errors="coerce")
        mean_val = float(serie.mean(skipna=True)) if serie.notna().any() else np.nan
        std_val = float(serie.std(skipna=True, ddof=0)) if serie.notna().any() else np.nan
        if not np.isfinite(std_val) or std_val < 1e-12:
            # sin variación: z=0 donde hay dato, NaN donde no hay
            z[col + "_ZS"] = np.where(serie.notna(), 0.0, np.nan)
        else:
            z[col + "_ZS"] = (serie - mean_val) / std_val
    return z


def main() -> None:
    print("=== GENERANDO SNAPSHOT Z-SCORES AVANZADO ===")
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        cols = columnas_objetivo(conn)
        print(f"Columnas objetivo ({len(cols)}): {cols}")

        # cargar datos base
        query = "SELECT CODIGO_MODULAR, NOMBRE_INSTITUCION, " + ", ".join(cols) + " FROM indices_metodologicos"
        df = pd.read_sql_query(query, conn)

        # calcular z-scores
        z = calcular_zscores(df, cols)
        out = pd.concat([df[["CODIGO_MODULAR"]], z], axis=1)

        # Materializar tabla
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS indices_zscores_avanzado")
        out.to_sql("indices_zscores_avanzado", conn, if_exists="replace", index=False)

        # Índice primario simple
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_zscores_cod ON indices_zscores_avanzado (CODIGO_MODULAR)"
        )
        conn.commit()

        # Resumen
        num_cols = len([c for c in out.columns if c.endswith("_ZS")])
        print(f"[OK] Tabla indices_zscores_avanzado creada: {len(out)} filas, {num_cols} columnas ZS")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


