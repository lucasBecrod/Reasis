#!/usr/bin/env python3
"""
Clustering Simple Metodológico - Proyecto Reasis
Implementa análisis de clustering simplificado para generar tipologías
de instituciones educativas usando K-Means básico con numpy.
"""

import pandas as pd
import sqlite3
import numpy as np

def kmeans_simple(X, k, max_iters=100, random_state=42):
    """Implementación simple de K-Means usando solo numpy"""
    np.random.seed(random_state)
    
    # Inicializar centroides aleatoriamente
    n_samples, n_features = X.shape
    centroids = X[np.random.choice(n_samples, k, replace=False)]
    
    for _ in range(max_iters):
        # Asignar puntos al centroide más cercano
        distances = np.sqrt(((X - centroids[:, np.newaxis])**2).sum(axis=2))
        labels = np.argmin(distances, axis=0)
        
        # Actualizar centroides
        new_centroids = np.array([X[labels == i].mean(axis=0) for i in range(k)])
        
        # Verificar convergencia
        if np.allclose(centroids, new_centroids):
            break
        centroids = new_centroids
    
    # Calcular inercia (suma de distancias cuadráticas)
    inertia = sum([np.sum((X[labels == i] - centroids[i])**2) for i in range(k)])
    
    return labels, centroids, inertia

def cargar_datos_clustering():
    """Cargar datos desde tabla indices_metodologicos"""
    print("=== CLUSTERING SIMPLE METODOLÓGICO ===")
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
    
    # Análisis de completitud
    variables_clustering = ['Y1_ILA_zscore', 'X1_NVC_zscore', 'X2_TR', 'X4_IDD_zscore', 'X11_RED_zscore']
    
    print(f"\n   COMPLETITUD POR VARIABLE:")
    for var in variables_clustering:
        if var in df_clustering.columns:
            count = df_clustering[var].notna().sum()
            pct = (count / len(df_clustering)) * 100
            print(f"     {var:15}: {count:3d} ({pct:5.1f}%)")
    
    return df_clustering

def preparar_datos_clustering(df):
    """Preparar matriz de datos para clustering"""
    print("\n2. PREPARANDO DATOS PARA CLUSTERING...")
    
    # Variables principales para clustering
    variables_core = ['Y1_ILA_zscore', 'X1_NVC_zscore', 'X2_TR', 'X4_IDD_zscore', 'X11_RED_zscore']
    
    # Crear matriz base
    df_work = df.copy()
    
    # Normalizar X2_TR (única variable no estandarizada)
    if 'X2_TR' in df_work.columns:
        x2_mean = df_work['X2_TR'].mean()
        x2_std = df_work['X2_TR'].std()
        df_work['X2_TR_norm'] = (df_work['X2_TR'] - x2_mean) / x2_std
        variables_core[2] = 'X2_TR_norm'  # Usar la versión normalizada
    
    # Filtrar instituciones con al menos 3 variables válidas
    df_work['vars_validas'] = df_work[variables_core].notna().sum(axis=1)
    df_filtered = df_work[df_work['vars_validas'] >= 3].copy()
    
    print(f"   Instituciones con ≥3 variables: {len(df_filtered)} (de {len(df)} total)")
    
    # Imputar valores faltantes con la media
    X_matrix = df_filtered[variables_core].copy()
    
    for col in variables_core:
        media = X_matrix[col].mean()
        X_matrix[col] = X_matrix[col].fillna(media)
        n_imputados = df_filtered[col].isnull().sum()
        if n_imputados > 0:
            print(f"     {col}: {n_imputados} valores imputados con media {media:.2f}")
    
    # Convertir a numpy array
    X = X_matrix.values
    
    print(f"   Matriz final: {X.shape} (filas x variables)")
    
    return df_filtered, X, variables_core, X_matrix

def ejecutar_clustering_multiples_k(X, k_range):
    """Ejecutar clustering para múltiples valores de k"""
    print(f"\n3. PROBANDO MÚLTIPLES VALORES DE K...")
    
    resultados_k = []
    
    for k in k_range:
        print(f"   Probando K={k}...")
        labels, centroids, inertia = kmeans_simple(X, k)
        
        # Calcular métrica de calidad simple (ratio intra/inter cluster)
        # Distancia promedio intra-cluster
        intra_distances = []
        for i in range(k):
            cluster_points = X[labels == i]
            if len(cluster_points) > 1:
                center = centroids[i]
                distances = np.sqrt(np.sum((cluster_points - center)**2, axis=1))
                intra_distances.extend(distances)
        
        avg_intra = np.mean(intra_distances) if intra_distances else 0
        
        # Distancia entre centroides (inter-cluster)
        inter_distances = []
        for i in range(k):
            for j in range(i+1, k):
                dist = np.sqrt(np.sum((centroids[i] - centroids[j])**2))
                inter_distances.append(dist)
        
        avg_inter = np.mean(inter_distances) if inter_distances else 1
        
        # Métrica de calidad: mayor inter/intra es mejor
        calidad = avg_inter / (avg_intra + 0.001)  # Evitar división por cero
        
        # Contar clusters no vacíos
        cluster_sizes = [np.sum(labels == i) for i in range(k)]
        clusters_validos = sum(1 for size in cluster_sizes if size > 0)
        
        resultado = {
            'k': k,
            'labels': labels,
            'centroids': centroids,
            'inertia': inertia,
            'calidad': calidad,
            'cluster_sizes': cluster_sizes,
            'clusters_validos': clusters_validos
        }
        
        resultados_k.append(resultado)
        
        print(f"     Inercia: {inertia:.2f}, Calidad: {calidad:.2f}, Clusters válidos: {clusters_validos}")
    
    # Seleccionar k óptimo (mejor balance entre calidad y simplicidad)
    scores = [(r['calidad'] - 0.1 * r['k']) for r in resultados_k]  # Penalizar muchos clusters
    mejor_idx = np.argmax(scores)
    k_optimo = resultados_k[mejor_idx]['k']
    
    print(f"\n   K ÓPTIMO SELECCIONADO: {k_optimo}")
    
    return resultados_k[mejor_idx], k_optimo

def caracterizar_clusters_simple(df_filtered, X_matrix, labels, centroids, k_optimo, variables_core):
    """Caracterizar clusters de forma simple"""
    print(f"\n4. CARACTERIZANDO {k_optimo} CLUSTERS...")
    
    df_clusters = df_filtered.copy()
    df_clusters['cluster'] = labels
    
    tipologias = {}
    
    for i in range(k_optimo):
        cluster_mask = labels == i
        cluster_data = df_filtered[cluster_mask]
        n_instituciones = len(cluster_data)
        
        if n_instituciones == 0:
            continue
            
        print(f"\n   === CLUSTER {i} ({n_instituciones} instituciones) ===")
        
        # Calcular promedios
        cluster_means = {}
        interpretaciones = {}
        
        for j, var in enumerate(variables_core):
            media = X_matrix[cluster_mask][var].mean()
            cluster_means[var] = media
            
            # Interpretación simple
            if 'zscore' in var:
                if media > 0.5:
                    nivel = "Alto"
                elif media > -0.5:
                    nivel = "Medio"
                else:
                    nivel = "Bajo"
            else:  # X2_TR_norm
                if media > 0.5:
                    nivel = "Muy Rural"
                elif media > -0.5:
                    nivel = "Rural/Mixto"
                else:
                    nivel = "Urbano"
            
            interpretaciones[var] = nivel
            print(f"     {var}: {media:.2f} ({nivel})")
        
        # Distribución por redes
        redes_cluster = cluster_data['numero_fya'].value_counts()
        print(f"     Redes principales: {dict(redes_cluster.head(3))}")
        
        # Crear tipología
        ila = interpretaciones.get('Y1_ILA_zscore', 'N/A')
        vulnerabilidad_raw = interpretaciones.get('X1_NVC_zscore', 'N/A')
        ruralidad = interpretaciones.get('X2_TR_norm', 'N/A')
        docentes = interpretaciones.get('X4_IDD_zscore', 'N/A')
        
        # Mapear vulnerabilidad (invertir lógica: alto NVC = alta vulnerabilidad)
        if vulnerabilidad_raw == "Alto":
            vulnerabilidad = "Alta"
        elif vulnerabilidad_raw == "Bajo":
            vulnerabilidad = "Baja"
        else:
            vulnerabilidad = "Media"
        
        # Generar nombre de tipología
        if ila == "Alto" and vulnerabilidad == "Baja":
            nombre = f"Instituciones de Alto Rendimiento ({ruralidad})"
        elif ila == "Bajo" and vulnerabilidad == "Alta":
            nombre = f"Instituciones que Requieren Intervención ({ruralidad})"
        elif ila == "Medio" and vulnerabilidad == "Alta":
            nombre = f"Instituciones Resilientes ({ruralidad})"
        elif ila == "Medio" and vulnerabilidad == "Media":
            nombre = f"Instituciones en Desarrollo ({ruralidad})"
        else:
            nombre = f"Instituciones Perfil Específico ({ruralidad})"
        
        tipologia = {
            'cluster_id': i,
            'nombre': nombre,
            'n_instituciones': n_instituciones,
            'porcentaje': (n_instituciones / len(df_filtered)) * 100,
            'caracteristicas': {
                'logro_academico': ila,
                'vulnerabilidad': vulnerabilidad,
                'contexto': ruralidad,
                'desempeno_docente': docentes
            },
            'promedios': cluster_means,
            'redes_principales': dict(redes_cluster.head(3))
        }
        
        tipologias[f'Cluster_{i}'] = tipologia
        
        print(f"     TIPOLOGÍA: {nombre}")
    
    return df_clusters, tipologias

def guardar_resultados_simple(df_clusters, tipologias, k_optimo):
    """Guardar resultados en base de datos"""
    print(f"\n5. GUARDANDO RESULTADOS...")
    
    conn = sqlite3.connect('reasis_database.db')
    cursor = conn.cursor()
    
    # Crear tabla
    cursor.execute("DROP TABLE IF EXISTS clustering_tipologias")
    cursor.execute("""
        CREATE TABLE clustering_tipologias (
            codigo_modular TEXT PRIMARY KEY,
            nombre_institucion TEXT,
            numero_fya TEXT,
            cluster_id INTEGER,
            tipologia_nombre TEXT,
            caracteristicas TEXT,
            
            -- Variables utilizadas
            Y1_ILA_zscore REAL,
            X1_NVC_zscore REAL,
            X2_TR_normalizado REAL,
            X4_IDD_zscore REAL,
            X11_RED_zscore REAL,
            
            -- Metadatos
            k_total INTEGER,
            fecha_analisis TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (codigo_modular) REFERENCES instituciones_educativas(codigo_modular)
        )
    """)
    
    # Insertar datos
    registros_insertados = 0
    for _, row in df_clusters.iterrows():
        cluster_id = row['cluster']
        
        if f'Cluster_{cluster_id}' in tipologias:
            tipologia = tipologias[f'Cluster_{cluster_id}']
            
            caracteristicas_str = f"Logro: {tipologia['caracteristicas']['logro_academico']}, " + \
                                f"Vulnerabilidad: {tipologia['caracteristicas']['vulnerabilidad']}, " + \
                                f"Contexto: {tipologia['caracteristicas']['contexto']}"
            
            cursor.execute("""
                INSERT INTO clustering_tipologias 
                (codigo_modular, nombre_institucion, numero_fya, cluster_id,
                 tipologia_nombre, caracteristicas, 
                 Y1_ILA_zscore, X1_NVC_zscore, X2_TR_normalizado, X4_IDD_zscore, X11_RED_zscore,
                 k_total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['codigo_modular'],
                row['nombre_institucion'],
                row['numero_fya'],
                cluster_id,
                tipologia['nombre'],
                caracteristicas_str,
                row.get('Y1_ILA_zscore'),
                row.get('X1_NVC_zscore'),
                row.get('X2_TR'),
                row.get('X4_IDD_zscore'),
                row.get('X11_RED_zscore'),
                k_optimo
            ))
            registros_insertados += 1
    
    conn.commit()
    conn.close()
    
    print(f"   [OK] {registros_insertados} resultados guardados en tabla clustering_tipologias")

def generar_reporte_final(tipologias):
    """Generar reporte final de tipologías"""
    print(f"\n6. REPORTE FINAL DE TIPOLOGÍAS...")
    
    conn = sqlite3.connect('reasis_database.db')
    
    # Resumen general
    query_resumen = """
        SELECT tipologia_nombre, COUNT(*) as instituciones,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM clustering_tipologias), 1) as porcentaje
        FROM clustering_tipologias
        GROUP BY cluster_id, tipologia_nombre
        ORDER BY cluster_id
    """
    
    df_resumen = pd.read_sql_query(query_resumen, conn)
    
    print(f"\n   TIPOLOGÍAS IDENTIFICADAS:")
    print("   " + "="*70)
    
    for _, row in df_resumen.iterrows():
        print(f"   {row['tipologia_nombre']}")
        print(f"     Instituciones: {row['instituciones']} ({row['porcentaje']}%)")
        print()
    
    # Análisis por redes del estudio
    query_redes = """
        SELECT numero_fya, tipologia_nombre, COUNT(*) as n
        FROM clustering_tipologias
        WHERE numero_fya IN ('44', '47', '48', '54', '72', '79')
        GROUP BY numero_fya, tipologia_nombre
        ORDER BY numero_fya, cluster_id
    """
    
    df_redes = pd.read_sql_query(query_redes, conn)
    
    if len(df_redes) > 0:
        print(f"   ANÁLISIS REDES DEL ESTUDIO:")
        print("   " + "-"*40)
        
        for red in ['44', '47', '48', '54', '72', '79']:
            red_data = df_redes[df_redes['numero_fya'] == red]
            if len(red_data) > 0:
                total_red = red_data['n'].sum()
                print(f"   Red {red} ({total_red} instituciones):")
                for _, row in red_data.iterrows():
                    print(f"     - {row['tipologia_nombre']}: {row['n']}")
                print()
    
    conn.close()
    
    total_tipologias = len(df_resumen)
    total_instituciones = df_resumen['instituciones'].sum()
    
    print(f"   RESUMEN FINAL:")
    print(f"     Tipologías generadas: {total_tipologias}")
    print(f"     Instituciones clasificadas: {total_instituciones}")
    print(f"     Variables utilizadas: 5 (estandarizadas)")
    
    return total_tipologias, total_instituciones

def main():
    """Función principal"""
    print("CLUSTERING SIMPLE METODOLÓGICO - PROYECTO REASIS")
    print("=" * 60)
    
    # 1. Cargar datos
    df_clustering = cargar_datos_clustering()
    
    # 2. Preparar datos
    df_filtered, X, variables_core, X_matrix = preparar_datos_clustering(df_clustering)
    
    # 3. Ejecutar clustering con múltiples k
    k_range = range(2, min(7, len(df_filtered)//10))  # Entre 2 y 6 clusters
    mejor_resultado, k_optimo = ejecutar_clustering_multiples_k(X, k_range)
    
    # 4. Caracterizar clusters
    df_clusters, tipologias = caracterizar_clusters_simple(
        df_filtered, X_matrix, mejor_resultado['labels'], 
        mejor_resultado['centroids'], k_optimo, variables_core
    )
    
    # 5. Guardar resultados
    guardar_resultados_simple(df_clusters, tipologias, k_optimo)
    
    # 6. Generar reporte
    n_tipologias, n_instituciones = generar_reporte_final(tipologias)
    
    print(f"\n[ÉXITO] Clustering metodológico completado:")
    print(f"  Tipologías: {n_tipologias}")
    print(f"  Instituciones: {n_instituciones}")
    print(f"  K óptimo: {k_optimo}")
    
    return tipologias, df_clusters

if __name__ == "__main__":
    tipologias, df_clusters = main()