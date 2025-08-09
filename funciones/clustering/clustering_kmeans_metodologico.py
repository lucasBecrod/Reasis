#!/usr/bin/env python3
"""
Clustering K-Means Metodológico - Proyecto Reasis
Implementa análisis de clustering para generar tipologías de instituciones educativas
usando las variables metodológicas estandarizadas disponibles.

VARIABLES DISPONIBLES (5.5/10):
- Y1_ILA_zscore: Índice Logro Académico (75 instituciones)
- X1_NVC_zscore: Vulnerabilidad Contextual (86 instituciones)
- X2_TR: Tipo Ruralidad (384 instituciones)
- X4_IDD_zscore: Desempeño Docente (66 instituciones)
- X11_RED_zscore: Ratio Estudiante-Docente (169 instituciones)
- Y2_TD: Tendencia Desempeño (34 instituciones - parcial)
"""

import pandas as pd
import sqlite3
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.impute import SimpleImputer
import matplotlib.pyplot as plt
import seaborn as sns

def cargar_datos_clustering():
    """Cargar datos desde tabla indices_metodologicos"""
    print("=== CLUSTERING K-MEANS METODOLÓGICO ===")
    print("1. CARGANDO DATOS METODOLÓGICOS...")
    
    conn = sqlite3.connect('reasis_database.db')
    
    query = """
        SELECT codigo_modular, nombre_institucion, numero_fya, nombre_red_fya_matched,
               Y1_ILA_zscore, Y2_TD, X1_NVC_zscore, X2_TR, 
               X4_IDD_zscore, X11_RED_zscore
        FROM indices_metodologicos
    """
    
    df_clustering = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"   Base cargada: {len(df_clustering)} instituciones")
    
    # Análisis de completitud por variable
    print(f"\n   COMPLETITUD POR VARIABLE:")
    variables_clustering = ['Y1_ILA_zscore', 'Y2_TD', 'X1_NVC_zscore', 'X2_TR', 'X4_IDD_zscore', 'X11_RED_zscore']
    
    for var in variables_clustering:
        if var in df_clustering.columns:
            count = df_clustering[var].notna().sum()
            pct = (count / len(df_clustering)) * 100
            print(f"     {var:15}: {count:3d} ({pct:5.1f}%)")
    
    return df_clustering

def preparar_matriz_clustering(df):
    """Preparar matriz de datos para clustering"""
    print("\n2. PREPARANDO MATRIZ DE CLUSTERING...")
    
    # Variables para clustering (solo numéricas)
    variables_numericas = ['Y1_ILA_zscore', 'X1_NVC_zscore', 'X2_TR', 'X4_IDD_zscore', 'X11_RED_zscore']
    
    # Filtrar instituciones con al menos 3 variables disponibles
    df_valid = df.copy()
    
    # Contar variables válidas por institución
    df_valid['vars_disponibles'] = df_valid[variables_numericas].notna().sum(axis=1)
    
    # Filtrar instituciones con suficientes datos (>=3 variables)
    df_filtered = df_valid[df_valid['vars_disponibles'] >= 3].copy()
    
    print(f"   Instituciones con >=3 variables: {len(df_filtered)} (de {len(df)} total)")
    print(f"   Variables numéricas seleccionadas: {len(variables_numericas)}")
    
    # Crear matriz de características
    X = df_filtered[variables_numericas].copy()
    
    # Imputar valores faltantes con la media
    imputer = SimpleImputer(strategy='mean')
    X_imputed = pd.DataFrame(
        imputer.fit_transform(X),
        columns=X.columns,
        index=X.index
    )
    
    # Estandarizar variables que no están ya estandarizadas (X2_TR)
    scaler = StandardScaler()
    X2_TR_scaled = scaler.fit_transform(X_imputed[['X2_TR']])
    X_imputed['X2_TR'] = X2_TR_scaled
    
    print(f"   Matriz final: {X_imputed.shape}")
    print(f"   Variables imputadas: {X.isnull().sum().sum()} valores faltantes")
    
    return df_filtered, X_imputed, variables_numericas

def determinar_k_optimo(X):
    """Determinar número óptimo de clusters usando método del codo y silhouette"""
    print("\n3. DETERMINANDO K ÓPTIMO...")
    
    k_range = range(2, min(8, max(3, len(X)//5)))  # Máximo 7 clusters o n/5, mínimo 3
    
    inertias = []
    silhouette_scores = []
    
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X)
        
        inertias.append(kmeans.inertia_)
        sil_score = silhouette_score(X, cluster_labels)
        silhouette_scores.append(sil_score)
        
        print(f"   K={k}: Inercia={kmeans.inertia_:.2f}, Silhouette={sil_score:.3f}")
    
    # Encontrar k óptimo por silhouette score
    k_optimo = k_range[np.argmax(silhouette_scores)]
    mejor_silhouette = max(silhouette_scores)
    
    print(f"\n   K ÓPTIMO: {k_optimo} (Silhouette: {mejor_silhouette:.3f})")
    
    return k_optimo, silhouette_scores

def ejecutar_clustering(X, k_optimo):
    """Ejecutar clustering K-Means con k óptimo"""
    print(f"\n4. EJECUTANDO CLUSTERING K-MEANS (K={k_optimo})...")
    
    kmeans = KMeans(n_clusters=k_optimo, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X)
    
    # Calcular métricas
    silhouette_avg = silhouette_score(X, cluster_labels)
    
    print(f"   Silhouette Score: {silhouette_avg:.3f}")
    print(f"   Inercia: {kmeans.inertia_:.2f}")
    
    # Análisis de clusters
    unique_labels, counts = np.unique(cluster_labels, return_counts=True)
    print(f"\n   DISTRIBUCIÓN DE CLUSTERS:")
    for label, count in zip(unique_labels, counts):
        pct = (count / len(cluster_labels)) * 100
        print(f"     Cluster {label}: {count} instituciones ({pct:.1f}%)")
    
    return kmeans, cluster_labels

def caracterizar_clusters(df_filtered, X, cluster_labels, variables_numericas, k_optimo):
    """Caracterizar y perfilar cada cluster"""
    print(f"\n5. CARACTERIZANDO CLUSTERS...")
    
    # Agregar labels al dataframe
    df_clusters = df_filtered.copy()
    df_clusters['cluster'] = cluster_labels
    
    # Calcular estadísticas por cluster
    cluster_profiles = []
    
    for i in range(k_optimo):
        cluster_data = df_clusters[df_clusters['cluster'] == i]
        n_instituciones = len(cluster_data)
        
        print(f"\n   === CLUSTER {i} ({n_instituciones} instituciones) ===")
        
        # Promedios de variables
        perfil = {'cluster': i, 'n_instituciones': n_instituciones}
        
        for var in variables_numericas:
            if var in X.columns:
                media = X[df_clusters['cluster'] == i][var].mean()
                perfil[f'{var}_media'] = media
                
                # Interpretación cualitativa
                if 'zscore' in var:
                    if media > 0.5:
                        nivel = "Alto"
                    elif media > -0.5:
                        nivel = "Medio"
                    else:
                        nivel = "Bajo"
                else:  # X2_TR
                    if media > 0.5:
                        nivel = "Muy Rural"
                    elif media > -0.5:
                        nivel = "Rural"
                    else:
                        nivel = "Urbano"
                
                print(f"     {var}: {media:.2f} ({nivel})")
        
        # Distribución por redes
        redes_dist = cluster_data['numero_fya'].value_counts()
        print(f"     Redes principales: {redes_dist.head(3).to_dict()}")
        
        # Características contextuales
        ruralidad = cluster_data.groupby('numero_fya').size()
        print(f"     Distribución geográfica: {len(ruralidad)} redes representadas")
        
        cluster_profiles.append(perfil)
    
    return df_clusters, cluster_profiles

def generar_tipologias_educativas(cluster_profiles, k_optimo):
    """Generar tipologías educativas interpretativas"""
    print(f"\n6. GENERANDO TIPOLOGÍAS EDUCATIVAS...")
    
    tipologias = {}
    
    for i in range(k_optimo):
        perfil = cluster_profiles[i]
        n_inst = perfil['n_instituciones']
        
        # Análisis multidimensional para tipología
        ila_nivel = "Alto" if perfil.get('Y1_ILA_zscore_media', 0) > 0.5 else \
                   "Medio" if perfil.get('Y1_ILA_zscore_media', 0) > -0.5 else "Bajo"
        
        vulnerabilidad = "Alta" if perfil.get('X1_NVC_zscore_media', 0) > 0.5 else \
                        "Media" if perfil.get('X1_NVC_zscore_media', 0) > -0.5 else "Baja"
        
        ruralidad = "Rural" if perfil.get('X2_TR_media', 0) > 0 else "Urbano"
        
        docentes = "Destacado" if perfil.get('X4_IDD_zscore_media', 0) > 0.5 else \
                  "Promedio" if perfil.get('X4_IDD_zscore_media', 0) > -0.5 else "Necesita apoyo"
        
        # Crear tipología descriptiva
        if ila_nivel == "Alto" and vulnerabilidad == "Baja":
            tipologia = f"Instituciones de Alto Rendimiento ({ruralidad})"
        elif ila_nivel == "Bajo" and vulnerabilidad == "Alta":
            tipologia = f"Instituciones que Requieren Intervención Integral ({ruralidad})"
        elif vulnerabilidad == "Alta" and ila_nivel == "Medio":
            tipologia = f"Instituciones Resilientes ({ruralidad})"
        elif ila_nivel == "Medio" and vulnerabilidad == "Media":
            tipologia = f"Instituciones en Desarrollo ({ruralidad})"
        else:
            tipologia = f"Instituciones Contexto Específico ({ruralidad})"
        
        caracteristicas = {
            'nombre': tipologia,
            'n_instituciones': n_inst,
            'porcentaje': (n_inst / sum(p['n_instituciones'] for p in cluster_profiles)) * 100,
            'ila_nivel': ila_nivel,
            'vulnerabilidad': vulnerabilidad,
            'contexto': ruralidad,
            'docentes': docentes,
            'perfil_completo': perfil
        }
        
        tipologias[f'Cluster_{i}'] = caracteristicas
        
        print(f"\n   {tipologia}")
        print(f"     N° Instituciones: {n_inst} ({caracteristicas['porcentaje']:.1f}%)")
        print(f"     Logro Académico: {ila_nivel}")
        print(f"     Vulnerabilidad: {vulnerabilidad}")
        print(f"     Contexto: {ruralidad}")
        print(f"     Desempeño Docente: {docentes}")
    
    return tipologias

def guardar_resultados_clustering(df_clusters, tipologias, k_optimo):
    """Guardar resultados en base de datos"""
    print(f"\n7. GUARDANDO RESULTADOS...")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # Crear tabla de resultados clustering (eliminar si existe)
    cursor.execute("DROP TABLE IF EXISTS resultados_clustering")
    cursor.execute("""
        CREATE TABLE resultados_clustering (
            codigo_modular TEXT PRIMARY KEY,
            nombre_institucion TEXT,
            numero_fya TEXT,
            cluster_asignado INTEGER,
            tipologia_nombre TEXT,
            tipologia_descripcion TEXT,
            n_variables_disponibles INTEGER,
            
            -- Variables utilizadas
            Y1_ILA_zscore REAL,
            X1_NVC_zscore REAL,
            X2_TR_normalizado REAL,
            X4_IDD_zscore REAL,
            X11_RED_zscore REAL,
            
            -- Metadatos
            k_clusters INTEGER,
            silhouette_score REAL,
            fecha_clustering TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (codigo_modular) REFERENCES instituciones_educativas(codigo_modular)
        )
    """)
    
    # Preparar datos para inserción masiva
    datos_insercion = []
    for _, row in df_clusters.iterrows():
        cluster_id = row['cluster']
        tipologia = tipologias[f'Cluster_{cluster_id}']
        
        datos_insercion.append((
            row['codigo_modular'],
            row['nombre_institucion'],
            row['numero_fya'],
            cluster_id,
            tipologia['nombre'],
            f"Logro: {tipologia['ila_nivel']}, Vulnerabilidad: {tipologia['vulnerabilidad']}, Contexto: {tipologia['contexto']}",
            row['vars_disponibles'],
            row.get('Y1_ILA_zscore'),
            row.get('X1_NVC_zscore'),
            row.get('X2_TR'),
            row.get('X4_IDD_zscore'), 
            row.get('X11_RED_zscore'),
            k_optimo
        ))
    
    # Insertar todos los datos de una vez
    cursor.executemany("""
        INSERT OR REPLACE INTO resultados_clustering 
        (codigo_modular, nombre_institucion, numero_fya, cluster_asignado,
         tipologia_nombre, tipologia_descripcion, n_variables_disponibles,
         Y1_ILA_zscore, X1_NVC_zscore, X2_TR_normalizado, X4_IDD_zscore, X11_RED_zscore,
         k_clusters)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, datos_insercion)
    
    conn.commit()
    conn.close()
    
    print(f"   [OK] {len(df_clusters)} resultados guardados en tabla resultados_clustering")

def generar_reporte_clustering():
    """Generar reporte final de clustering"""
    print(f"\n8. GENERANDO REPORTE FINAL...")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Resumen por tipologías
    query_resumen = """
        SELECT tipologia_nombre, COUNT(*) as instituciones,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM resultados_clustering), 1) as porcentaje
        FROM resultados_clustering
        GROUP BY tipologia_nombre, cluster_asignado
        ORDER BY cluster_asignado
    """
    
    df_resumen = pd.read_sql_query(query_resumen, conn)
    
    print(f"\nRESUMEN TIPOLOGÍAS GENERADAS:")
    print("=" * 80)
    
    for _, row in df_resumen.iterrows():
        print(f"{row['tipologia_nombre']}")
        print(f"  Instituciones: {row['instituciones']} ({row['porcentaje']}%)")
        print()
    
    # Distribución por redes
    query_redes = """
        SELECT numero_fya, tipologia_nombre, COUNT(*) as instituciones
        FROM resultados_clustering
        WHERE numero_fya IN ('44', '47', '48', '54', '72', '79')
        GROUP BY numero_fya, tipologia_nombre
        ORDER BY numero_fya, cluster_asignado
    """
    
    df_redes = pd.read_sql_query(query_redes, conn)
    
    print(f"DISTRIBUCIÓN POR REDES DEL ESTUDIO:")
    print("-" * 50)
    
    for red in ['44', '47', '48', '54', '72', '79']:
        red_data = df_redes[df_redes['numero_fya'] == red]
        if len(red_data) > 0:
            total_red = red_data['instituciones'].sum()
            print(f"Red {red} ({total_red} instituciones):")
            for _, row in red_data.iterrows():
                print(f"  - {row['tipologia_nombre']}: {row['instituciones']}")
        print()
    
    conn.close()
    
    return len(df_resumen)

def main():
    """Función principal de clustering"""
    print("CLUSTERING K-MEANS METODOLÓGICO - PROYECTO REASIS")
    print("=" * 60)
    
    # 1. Cargar datos
    df_clustering = cargar_datos_clustering()
    
    # 2. Preparar matriz
    df_filtered, X_imputed, variables_numericas = preparar_matriz_clustering(df_clustering)
    
    # 3. Determinar K óptimo
    k_optimo, silhouette_scores = determinar_k_optimo(X_imputed)
    
    # 4. Ejecutar clustering
    kmeans, cluster_labels = ejecutar_clustering(X_imputed, k_optimo)
    
    # 5. Caracterizar clusters
    df_clusters, cluster_profiles = caracterizar_clusters(
        df_filtered, X_imputed, cluster_labels, variables_numericas, k_optimo
    )
    
    # 6. Generar tipologías
    tipologias = generar_tipologias_educativas(cluster_profiles, k_optimo)
    
    # 7. Guardar resultados
    guardar_resultados_clustering(df_clusters, tipologias, k_optimo)
    
    # 8. Generar reporte
    n_tipologias = generar_reporte_clustering()
    
    print(f"\n[COMPLETADO] Clustering ejecutado: {n_tipologias} tipologías generadas")
    print(f"Instituciones analizadas: {len(df_clusters)}")
    print(f"Variables utilizadas: {len(variables_numericas)}")
    
    return tipologias, df_clusters

if __name__ == "__main__":
    tipologias, df_clusters = main()