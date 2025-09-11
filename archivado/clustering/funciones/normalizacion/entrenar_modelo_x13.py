import os
import json
from datetime import datetime
import sqlite3
import pandas as pd
import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
import joblib


def cargar_columnas(conn: sqlite3.Connection, tabla: str) -> set[str]:
    df = pd.read_sql_query(f"PRAGMA table_info({tabla})", conn)
    return set(df['name'].tolist())


def construir_dataset(conn: sqlite3.Connection) -> tuple[pd.DataFrame, pd.Series, dict]:
    cols_ie = cargar_columnas(conn, 'instituciones_educativas')
    cols_idx = cargar_columnas(conn, 'indices_metodologicos')

    # Target disponible: X13_TMATRC ya aplicado en parte
    q = """
    SELECT 
        idx.CODIGO_MODULAR as codigo_modular,
        idx.Y1_ILA, idx.Y2_TD, idx.X11_RED,
        idx.X13_TMATRC, idx.X13_TMATRC_CATEGORIA,
        ie.nombre_red_fya_matched, ie.numero_fya,
        ie.area_censo, ie.modalidad_especifica, ie.region, ie.provincia, ie.distrito,
        ie.total_alumnos, ie.total_docentes,
        ie.latitud, ie.longitud, ie.altitud
    FROM indices_metodologicos idx
    LEFT JOIN instituciones_educativas ie
        ON ie.codigo_modular = idx.CODIGO_MODULAR
    """
    df = pd.read_sql_query(q, conn)

    # Seleccionar features candidatas según disponibilidad real
    candidate_cats = [
        'nombre_red_fya_matched', 'numero_fya', 'area_censo', 'modalidad_especifica',
        'region', 'provincia', 'distrito'
    ]
    candidate_nums = [
        'Y1_ILA', 'Y2_TD', 'X11_RED', 'total_alumnos', 'total_docentes',
        'latitud', 'longitud', 'altitud'
    ]

    available_features = [c for c in candidate_cats + candidate_nums if c in df.columns]
    if not available_features:
        return pd.DataFrame(), pd.Series(dtype=float), {'features': []}

    X = df[available_features].copy()
    y = df['X13_TMATRC']

    cats = [c for c in candidate_cats if c in X.columns]
    nums = [c for c in candidate_nums if c in X.columns]

    meta = {
        'features': available_features,
        'cats': cats,
        'nums': nums,
        'n_total': int(len(df)),
        'n_target_disponible': int(y.notna().sum())
    }
    return X, y, meta


def entrenar_guardar_modelo():
    os.makedirs('data/intermedios', exist_ok=True)
    conn = sqlite3.connect('reasis_database.db')
    try:
        X, y, meta = construir_dataset(conn)
        if X.empty or y.notna().sum() < 30:
            print('Datos insuficientes para entrenar modelo de imputación X13_TMATRC.')
            return

        # Usar solo filas con target disponible
        mask = y.notna()
        X_train = X.loc[mask].copy()
        y_train = y.loc[mask].astype(float)

        # Preprocesamiento
        cats = meta['cats']
        nums = meta['nums']
        preproc = ColumnTransformer(
            transformers=[
                ('cat', OneHotEncoder(handle_unknown='ignore'), cats),
                ('num', SimpleImputer(strategy='median'), nums)
            ],
            remainder='drop'
        )

        # Modelos
        models = {
            'knn_k7': KNeighborsRegressor(n_neighbors=7),
            'rf_200': RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
        }

        results = {}
        best_name = None
        best_mae = float('inf')
        best_pipeline = None
        for name, model in models.items():
            pipe = Pipeline(steps=[('pre', preproc), ('model', model)])
            scores = -cross_val_score(pipe, X_train, y_train, cv=5, scoring='neg_mean_absolute_error')
            mae = float(np.mean(scores))
            results[name] = {
                'mae_cv_mean': mae,
                'mae_cv_std': float(np.std(scores))
            }
            if mae < best_mae:
                best_mae = mae
                best_name = name
                best_pipeline = pipe

        # Entrenar mejor modelo y guardar
        best_pipeline.fit(X_train, y_train)
        model_path = 'data/intermedios/x13_tmatrc_model.pkl'
        joblib.dump({'pipeline': best_pipeline, 'meta': meta}, model_path)

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        metrics = {
            'timestamp': ts,
            'n_train': int(len(X_train)),
            'features': meta,
            'model_selection': results,
            'best_model': best_name,
            'best_mae_cv': best_mae
        }
        metrics_path = f'data/intermedios/x13_tmatrc_model_metrics_{ts}.json'
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)

        print(f"Modelo guardado en: {model_path}")
        print(f"Métricas CV: {metrics_path}")

    finally:
        conn.close()


if __name__ == '__main__':
    entrenar_guardar_modelo()


