#!/usr/bin/env python3
"""
Clustering K-Means Avanzado - Proyecto Reasis

Genera tipologías institucionales usando TODAS las variables disponibles en
`indices_metodologicos` (variables metodológicas Y/X y contextuales X14-X25).

Características:
- Selección dinámica de variables numéricas existentes en la tabla
- Filtro por completitud mínima configurable
- Imputación por mediana y estandarización (z-score)
- Selección de K por silhouette en rango 2..7
- Escritura de resultados a SQLite: `resultados_clustering_avanzado`
- Resumen por cluster: centroides y conteos (tabla `resumen_clusters_avanzado`)

Requisitos: pandas, numpy, scikit-learn
"""

from __future__ import annotations

import math
import sqlite3
from typing import List, Tuple, Dict

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


DATABASE_PATH = "reasis_database.db"


def obtener_columnas_disponibles(conn: sqlite3.Connection) -> Tuple[List[str], List[str]]:
    """Obtiene dinámicamente las columnas candidatas para clustering.

    Regresa dos listas: variables_metodologicas, variables_contextuales.
    Solo incluye columnas que existen actualmente en `indices_metodologicos`.
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(indices_metodologicos)")
    columnas = [row[1] for row in cursor.fetchall()]

    # Núcleo metodológico (preferir versiones finales no duplicadas)
    candidatas_metodologicas = [
        # Dependientes
        "Y1_ILA", "Y2_TD", "Y3_PR",
        # Independientes clave
        "X1_NVC", "X2_TR", "X4_IDD", "X6_CDD", "X10_IE",
        # Ratio y matrícula (usar columnas finales si existen)
        "X11_RED", "X11_RED_ajustado", "X12_TOE", "X13_TMATRC",
    ]

    # Variables contextuales integradas (X14-X25 y variantes renombradas)
    candidatas_contexto = [
        "X14_NIVEL_EDUCATIVO", "X16_MODALIDAD", "X17_GESTION", "X18_TURNO",
        "X19_ORGANIZACION_PEDAGOGICA", "X20_DIRECTIVOS_TOTAL", "X21_MULTIPLICIDAD1",
        "X22_MULTIPLICIDAD2", "X23_POBREZA_DISTRITO", "X24_GPMD", "X25_POBLACION_DISTRITO",
    ]

    # Conservar solo columnas existentes
    metodologicas = [c for c in candidatas_metodologicas if c in columnas]
    contextuales = [c for c in candidatas_contexto if c in columnas]

    # Evitar duplicidad entre X11_RED y X11_RED_ajustado: priorizar ajustado
    if "X11_RED_ajustado" in metodologicas and "X11_RED" in metodologicas:
        metodologicas.remove("X11_RED")

    return metodologicas, contextuales


def cargar_datos(conn: sqlite3.Connection, vars_met: List[str], vars_ctx: List[str]) -> pd.DataFrame:
    """Carga desde SQLite las columnas requeridas y metadatos básicos."""
    columnas_sql = [
        "CODIGO_MODULAR", "NOMBRE_INSTITUCION", "NUMERO_FYA", "X2_TR",
    ]
    seleccion = list(dict.fromkeys(columnas_sql + vars_met + vars_ctx))
    query = f"SELECT {', '.join(seleccion)} FROM indices_metodologicos"
    df = pd.read_sql_query(query, conn)
    return df


def preparar_matriz(df: pd.DataFrame, columnas_entrada: List[str], completitud_minima_ratio: float = 0.6) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """Convierte columnas a numéricas, filtra por completitud mínima,
    imputa por mediana y estandariza. Retorna df_filtrado, X_estandarizado, columnas_usadas.
    """
    df_work = df.copy()

    # Convertir todo a numérico cuando sea posible
    for col in columnas_entrada:
        if col in df_work.columns:
            df_work[col] = pd.to_numeric(df_work[col], errors="coerce")

    # Eliminar columnas con varianza cero o completamente nulas
    columnas_validas = []
    for col in columnas_entrada:
        serie = df_work[col]
        if serie.notna().sum() == 0:
            continue
        # Varianza sobre valores no nulos
        if serie.dropna().nunique() <= 1:
            continue
        columnas_validas.append(col)

    if not columnas_validas:
        raise RuntimeError("No hay columnas válidas para clustering tras validación de varianza.")

    # Filtro por completitud mínima por fila
    min_validas = max(1, math.ceil(len(columnas_validas) * completitud_minima_ratio))
    df_work["_validas"] = df_work[columnas_validas].notna().sum(axis=1)
    df_filtrado = df_work[df_work["_validas"] >= min_validas].drop(columns=["_validas"]).copy()

    if len(df_filtrado) < 5:
        raise RuntimeError("Muy pocas instituciones cumplen el umbral de completitud para clustering.")

    # Imputación por mediana
    imputer = SimpleImputer(strategy="median")
    X_imputado = pd.DataFrame(
        imputer.fit_transform(df_filtrado[columnas_validas]),
        columns=columnas_validas,
        index=df_filtrado.index,
    )

    # Estandarización
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(
        scaler.fit_transform(X_imputado),
        columns=columnas_validas,
        index=df_filtrado.index,
    )

    return df_filtrado, X_scaled, columnas_validas


def seleccionar_k_optimo(X: pd.DataFrame) -> Tuple[int, Dict[int, float]]:
    """Evalúa silhouette para K en 2..7 (acotado por tamaño)."""
    max_k = max(2, min(7, len(X) - 1))
    rangos = range(2, max_k + 1)
    resultados: Dict[int, float] = {}

    for k in rangos:
        modelo = KMeans(n_clusters=k, random_state=42, n_init=10)
        etiquetas = modelo.fit_predict(X)
        try:
            sil = float(silhouette_score(X, etiquetas))
        except Exception:
            sil = -1.0
        resultados[k] = sil

    k_optimo = max(resultados, key=resultados.get)
    return k_optimo, resultados


def etiquetar_tipologia(centroide: pd.Series) -> str:
    """Genera una etiqueta simple basada en algunos ejes conceptuales si existen."""
    def nivel(v: float) -> str:
        if v >= 0.5:
            return "Alto"
        if v <= -0.5:
            return "Bajo"
        return "Medio"

    partes = []
    for clave, nombre in [
        ("Y1_ILA", "Logro"),
        ("X1_NVC", "Vulnerabilidad"),
        ("X2_TR", "Ruralidad"),
        ("X4_IDD", "Docentes"),
        ("X10_IE", "Infraestructura"),
        ("X11_RED", "Ratio"),
        ("X11_RED_ajustado", "Ratio"),
        ("X13_TMATRC", "Matrícula"),
    ]:
        if clave in centroide.index:
            partes.append(f"{nombre}:{nivel(float(centroide[clave]))}")

    return " | ".join(partes) if partes else "Perfil institucional"


def guardar_resultados(
    conn: sqlite3.Connection,
    df_base: pd.DataFrame,
    etiquetas: np.ndarray,
    k: int,
    silhouette: float,
    X: pd.DataFrame,
):
    """Crea/actualiza tablas de resultados en SQLite."""
    cursor = conn.cursor()

    # Crear tabla principal
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS resultados_clustering_avanzado (
            codigo_modular TEXT PRIMARY KEY,
            nombre_institucion TEXT,
            numero_fya TEXT,
            cluster_asignado INTEGER,
            k_clusters INTEGER,
            silhouette_score REAL,
            tipologia_label TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Crear tabla de resumen de centroides
    cursor.execute("DROP TABLE IF EXISTS resumen_clusters_avanzado")
    # Construir esquema dinámico para centroides (una columna por variable)
    columnas_sql = ",\n            ".join([f'"{c}" REAL' for c in X.columns.tolist()])
    cursor.execute(
        f"""
        CREATE TABLE resumen_clusters_avanzado (
            cluster_id INTEGER PRIMARY KEY,
            n_instituciones INTEGER,
            {columnas_sql},
            tipologia_label TEXT
        )
        """
    )

    # Calcular centroides en espacio estandarizado (medias por cluster)
    df_labels = pd.Series(etiquetas, index=X.index, name="cluster")
    df_centroides = X.join(df_labels).groupby("cluster").mean()
    df_sizes = df_labels.value_counts().sort_index()

    # Insertar resumen por cluster
    for cluster_id in df_centroides.index.tolist():
        centroide = df_centroides.loc[cluster_id]
        label = etiquetar_tipologia(centroide)
        valores = [int(cluster_id), int(df_sizes.get(cluster_id, 0))]
        valores.extend([float(centroide[c]) for c in X.columns.tolist()])
        valores.append(label)

        placeholders = ", ".join(["?"] * len(valores))
        cursor.execute(
            f"INSERT OR REPLACE INTO resumen_clusters_avanzado VALUES ({placeholders})",
            valores,
        )

    # Insertar/actualizar resultados individuales
    datos = []
    for idx in X.index.tolist():
        row = df_base.loc[idx]
        datos.append(
            (
                str(row.get("CODIGO_MODULAR")),
                str(row.get("NOMBRE_INSTITUCION", ""))[:255],
                str(row.get("NUMERO_FYA", "")),
                int(df_labels.loc[idx]),
                int(k),
                float(silhouette),
                None,  # tipologia_label se une vía resumen si se requiere
            )
        )

    cursor.executemany(
        """
        INSERT OR REPLACE INTO resultados_clustering_avanzado
            (codigo_modular, nombre_institucion, numero_fya, cluster_asignado,
             k_clusters, silhouette_score, tipologia_label)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        datos,
    )

    conn.commit()


def main() -> Tuple[int, float, int]:
    print("=== CLUSTERING K-MEANS AVANZADO - PROYECTO REASIS ===")
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        # 1) Columnas disponibles
        vars_met, vars_ctx = obtener_columnas_disponibles(conn)
        print(f"Variables metodológicas encontradas: {len(vars_met)} -> {vars_met}")
        print(f"Variables contextuales encontradas: {len(vars_ctx)} -> {vars_ctx}")

        columnas_entrada = vars_met + vars_ctx
        if not columnas_entrada:
            raise RuntimeError("No hay columnas de entrada disponibles en indices_metodologicos.")

        # 2) Cargar datos
        df = cargar_datos(conn, vars_met, vars_ctx)
        print(f"Instituciones en BD: {len(df)}")

        # 3) Preparar matriz
        df_filtrado, X, columnas_usadas = preparar_matriz(df, columnas_entrada, completitud_minima_ratio=0.6)
        print(f"Instituciones en clustering: {len(df_filtrado)}")
        print(f"Columnas usadas: {len(columnas_usadas)} -> {columnas_usadas}")

        # 4) Seleccionar K
        k, resultados = seleccionar_k_optimo(X)
        print("Silhouette por K:", {kk: round(vv, 3) for kk, vv in resultados.items()})

        # 5) Entrenar KMeans final
        modelo = KMeans(n_clusters=k, random_state=42, n_init=10)
        etiquetas = modelo.fit_predict(X)
        silhouette_avg = float(silhouette_score(X, etiquetas))
        print(f"K óptimo: {k}  |  Silhouette: {silhouette_avg:.3f}")

        # 6) Guardar resultados
        guardar_resultados(conn, df_filtrado, etiquetas, k, silhouette_avg, X)

        print("[OK] Resultados guardados en resultados_clustering_avanzado y resumen_clusters_avanzado")
        return k, silhouette_avg, len(df_filtrado)
    finally:
        conn.close()


if __name__ == "__main__":
    main()


