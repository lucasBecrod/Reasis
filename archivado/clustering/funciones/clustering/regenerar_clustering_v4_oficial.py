#!/usr/bin/env python3
"""
Regenerar Clustering v4 - Solo IIEE RER Oficiales
Recalcula z-scores y clustering con las 163 IIEE RER confirmadas oficialmente
"""

import sqlite3
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from pathlib import Path
import logging

DATABASE_V4_PATH = "reasis_database_v4.db"

def setup_logging():
    """Configurar logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data/reports/clustering_v4_oficial.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def obtener_variables_disponibles(conn):
    """Obtener variables disponibles en indices_metodologicos"""
    logger = logging.getLogger(__name__)
    
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(indices_metodologicos)")
    columnas = [row[1] for row in cursor.fetchall()]
    
    # Variables metodológicas principales
    variables_metodologicas = [
        "Y1_ILA", "Y2_TD", "Y3_PR",
        "X1_NVC", "X2_TR", "X4_IDD", "X6_CDD", "X10_IE",
        "X11_RED", "X12_TOE", "X13_TMATRC", "X15_MEIB"
    ]
    
    # Variables contextuales
    variables_contextuales = [
        "X14_NIVEL_EDUCATIVO", "X16_MODALIDAD", "X17_GESTION", "X18_TURNO",
        "X19_ORGANIZACION_PEDAGOGICA", "X20_DIRECTIVOS_TOTAL", 
        "X21_MULTIPLICIDAD1", "X22_MULTIPLICIDAD2", 
        "X24_GPMD", "X25_POBLACION_DISTRITO"
    ]
    
    # Filtrar solo variables existentes
    variables_disponibles = [var for var in variables_metodologicas + variables_contextuales if var in columnas]
    
    logger.info(f"Variables disponibles para clustering: {len(variables_disponibles)}")
    logger.info(f"Variables: {variables_disponibles}")
    
    return variables_disponibles

def cargar_datos_oficiales(conn, variables):
    """Cargar datos solo de IIEE RER oficiales"""
    logger = logging.getLogger(__name__)
    
    # Construir query con variables disponibles
    columnas_sql = ["CODIGO_MODULAR", "NUMERO_FYA"] + variables
    query = f"SELECT {', '.join(columnas_sql)} FROM indices_metodologicos"
    
    df = pd.read_sql_query(query, conn)
    logger.info(f"IIEE cargadas para clustering: {len(df)}")
    
    # Verificar que todas sean RER
    df['NUMERO_FYA'] = df['NUMERO_FYA'].astype(str)
    rer_count = df[df['NUMERO_FYA'].str.contains('RER', na=False)].shape[0]
    logger.info(f"IIEE RER confirmadas: {rer_count}/{len(df)}")
    
    return df

def preparar_datos_clustering(df, variables, completitud_minima=0.6):
    """Preparar datos para clustering con limpieza y estandarización"""
    logger = logging.getLogger(__name__)
    
    df_work = df.copy()
    
    # Convertir variables a numérico
    for var in variables:
        if var in df_work.columns:
            df_work[var] = pd.to_numeric(df_work[var], errors='coerce')
    
    # Filtrar variables con varianza suficiente
    variables_validas = []
    for var in variables:
        if var in df_work.columns:
            serie = df_work[var]
            if serie.notna().sum() > 0 and serie.dropna().nunique() > 1:
                variables_validas.append(var)
    
    logger.info(f"Variables válidas para clustering: {len(variables_validas)}")
    
    # Filtrar instituciones con completitud mínima
    min_variables = max(1, int(len(variables_validas) * completitud_minima))
    df_work['completitud'] = df_work[variables_validas].notna().sum(axis=1)
    df_filtrado = df_work[df_work['completitud'] >= min_variables].copy()
    
    logger.info(f"IIEE con completitud >= {completitud_minima:.1%}: {len(df_filtrado)}")
    
    # Imputación y estandarización
    imputer = SimpleImputer(strategy='median')
    scaler = StandardScaler()
    
    X_imputado = pd.DataFrame(
        imputer.fit_transform(df_filtrado[variables_validas]),
        columns=variables_validas,
        index=df_filtrado.index
    )
    
    X_escalado = pd.DataFrame(
        scaler.fit_transform(X_imputado),
        columns=variables_validas,
        index=df_filtrado.index
    )
    
    logger.info(f"Datos preparados: {X_escalado.shape[0]} IIEE x {X_escalado.shape[1]} variables")
    
    return df_filtrado, X_escalado, variables_validas

def aplicar_pca(X, varianza_objetivo=0.90):
    """Aplicar PCA para reducción dimensional"""
    logger = logging.getLogger(__name__)
    
    pca = PCA()
    pca.fit(X)
    
    # Encontrar número de componentes para varianza objetivo
    varianza_acumulada = np.cumsum(pca.explained_variance_ratio_)
    n_componentes = np.searchsorted(varianza_acumulada, varianza_objetivo) + 1
    
    # Aplicar PCA con número óptimo de componentes
    pca_final = PCA(n_components=n_componentes)
    X_pca = pca_final.fit_transform(X)
    
    logger.info(f"PCA aplicado: {n_componentes} componentes explican {varianza_acumulada[n_componentes-1]:.3f} de varianza")
    
    return X_pca, pca_final

def evaluar_k_optimo(X, k_min=2, k_max=8):
    """Evaluar K óptimo usando múltiples métricas"""
    logger = logging.getLogger(__name__)
    
    max_k = min(k_max, len(X) - 1)
    resultados = []
    
    for k in range(k_min, max_k + 1):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        
        silhouette = silhouette_score(X, labels)
        davies_bouldin = davies_bouldin_score(X, labels)
        calinski_harabasz = calinski_harabasz_score(X, labels)
        
        resultados.append({
            'k': k,
            'silhouette': silhouette,
            'davies_bouldin': davies_bouldin,
            'calinski_harabasz': calinski_harabasz
        })
    
    df_resultados = pd.DataFrame(resultados)
    
    # Ranking combinado (silhouette↑, calinski_harabasz↑, davies_bouldin↓)
    df_resultados['rank_sil'] = df_resultados['silhouette'].rank(ascending=False)
    df_resultados['rank_ch'] = df_resultados['calinski_harabasz'].rank(ascending=False)
    df_resultados['rank_db'] = df_resultados['davies_bouldin'].rank(ascending=True)
    df_resultados['rank_total'] = df_resultados['rank_sil'] + df_resultados['rank_ch'] + df_resultados['rank_db']
    
    k_optimo = df_resultados.loc[df_resultados['rank_total'].idxmin(), 'k']
    
    logger.info(f"Evaluación de K completada. K óptimo: {k_optimo}")
    logger.info("Métricas por K:")
    for _, row in df_resultados.iterrows():
        logger.info(f"  K={row['k']}: Silhouette={row['silhouette']:.3f}, DB={row['davies_bouldin']:.3f}, CH={row['calinski_harabasz']:.1f}")
    
    return int(k_optimo), df_resultados

def aplicar_clustering_final(X, k, df_base):
    """Aplicar clustering final con K óptimo"""
    logger = logging.getLogger(__name__)
    
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    
    # Calcular métricas finales
    silhouette_final = silhouette_score(X, labels)
    davies_bouldin_final = davies_bouldin_score(X, labels)
    calinski_harabasz_final = calinski_harabasz_score(X, labels)
    
    logger.info(f"Clustering final aplicado:")
    logger.info(f"  K={k}, Silhouette={silhouette_final:.3f}")
    logger.info(f"  Davies-Bouldin={davies_bouldin_final:.3f}")
    logger.info(f"  Calinski-Harabasz={calinski_harabasz_final:.1f}")
    
    # Crear DataFrame de resultados
    df_resultados = df_base.copy()
    df_resultados['cluster'] = labels
    df_resultados['k_clusters'] = k
    df_resultados['silhouette_score'] = silhouette_final
    
    # Estadísticas por cluster
    distribucion = pd.Series(labels).value_counts().sort_index()
    logger.info("Distribución por cluster:")
    for cluster_id, count in distribucion.items():
        porcentaje = (count / len(labels)) * 100
        logger.info(f"  Cluster {cluster_id}: {count} IIEE ({porcentaje:.1f}%)")
    
    return df_resultados, kmeans, {
        'silhouette': silhouette_final,
        'davies_bouldin': davies_bouldin_final,
        'calinski_harabasz': calinski_harabasz_final
    }

def guardar_resultados_v4(conn, df_resultados, metricas, variables_usadas):
    """Guardar resultados en BD v4"""
    logger = logging.getLogger(__name__)
    
    cursor = conn.cursor()
    
    # Crear tabla de resultados v4
    cursor.execute("DROP TABLE IF EXISTS resultados_clustering_v4_oficial")
    cursor.execute("""
        CREATE TABLE resultados_clustering_v4_oficial (
            codigo_modular TEXT PRIMARY KEY,
            numero_fya TEXT,
            cluster_asignado INTEGER,
            k_clusters INTEGER,
            silhouette_score REAL,
            fecha_clustering TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insertar resultados
    for _, row in df_resultados.iterrows():
        cursor.execute("""
            INSERT OR REPLACE INTO resultados_clustering_v4_oficial 
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            str(row['CODIGO_MODULAR']),
            str(row['NUMERO_FYA']),
            int(row['cluster']),
            int(row['k_clusters']),
            float(row['silhouette_score'])
        ))
    
    # Crear tabla de resumen
    cursor.execute("DROP TABLE IF EXISTS resumen_clustering_v4_oficial")
    cursor.execute("""
        CREATE TABLE resumen_clustering_v4_oficial (
            cluster_id INTEGER PRIMARY KEY,
            n_instituciones INTEGER,
            porcentaje REAL
        )
    """)
    
    # Insertar resumen
    distribucion = df_resultados['cluster'].value_counts().sort_index()
    total = len(df_resultados)
    
    for cluster_id, count in distribucion.items():
        porcentaje = (count / total) * 100
        cursor.execute("""
            INSERT OR REPLACE INTO resumen_clustering_v4_oficial VALUES (?, ?, ?)
        """, (int(cluster_id), int(count), float(porcentaje)))
    
    # Guardar metadatos
    cursor.execute("DROP TABLE IF EXISTS metadatos_clustering_v4")
    cursor.execute("""
        CREATE TABLE metadatos_clustering_v4 (
            parametro TEXT PRIMARY KEY,
            valor TEXT
        )
    """)
    
    metadatos = {
        'total_iiee': str(len(df_resultados)),
        'k_clusters': str(df_resultados['k_clusters'].iloc[0]),
        'silhouette_score': str(metricas['silhouette']),
        'davies_bouldin': str(metricas['davies_bouldin']),
        'calinski_harabasz': str(metricas['calinski_harabasz']),
        'variables_usadas': ','.join(variables_usadas),
        'num_variables': str(len(variables_usadas))
    }
    
    for parametro, valor in metadatos.items():
        cursor.execute("INSERT OR REPLACE INTO metadatos_clustering_v4 VALUES (?, ?)", 
                      (parametro, valor))
    
    conn.commit()
    logger.info("Resultados guardados en BD v4 oficial")

def main():
    """Función principal"""
    logger = setup_logging()
    
    logger.info("=== INICIANDO CLUSTERING v4 CON IIEE RER OFICIALES ===")
    
    try:
        with sqlite3.connect(DATABASE_V4_PATH) as conn:
            # 1. Obtener variables disponibles
            variables = obtener_variables_disponibles(conn)
            
            if not variables:
                raise ValueError("No hay variables disponibles para clustering")
            
            # 2. Cargar datos oficiales
            df = cargar_datos_oficiales(conn, variables)
            
            # 3. Preparar datos
            df_limpio, X_escalado, variables_validas = preparar_datos_clustering(df, variables)
            
            # 4. Aplicar PCA
            X_pca, pca_model = aplicar_pca(X_escalado, varianza_objetivo=0.90)
            
            # 5. Evaluar K óptimo
            k_optimo, evaluacion_k = evaluar_k_optimo(X_pca)
            
            # 6. Clustering final
            df_resultados, kmeans_model, metricas = aplicar_clustering_final(
                X_pca, k_optimo, df_limpio
            )
            
            # 7. Guardar resultados
            guardar_resultados_v4(conn, df_resultados, metricas, variables_validas)
            
            # 8. Guardar evaluación K
            evaluacion_k.to_csv('data/reports/evaluacion_k_v4_oficial.csv', index=False)
            
            logger.info("=== CLUSTERING v4 OFICIAL COMPLETADO EXITOSAMENTE ===")
            
            return {
                'total_iiee': len(df_resultados),
                'k_optimo': k_optimo,
                'variables_usadas': len(variables_validas),
                'metricas': metricas
            }
    
    except Exception as e:
        logger.error(f"Error en clustering v4: {e}")
        return None

if __name__ == "__main__":
    resultado = main()