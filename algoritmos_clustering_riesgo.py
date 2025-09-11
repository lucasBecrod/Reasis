import pandas as pd
import numpy as np
import sqlite3
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

def cargar_datos_desde_sql():
    """
    Carga los datos desde la base de datos SQL v5
    """
    db_path = r"archivado\clustering\02 Informe Entregado\Anexo B - Base de datos SQL v5.db"
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Cargar tabla de índices metodológicos
        query = "SELECT * FROM indices_metodologicos"
        df = pd.read_sql_query(query, conn)
        
        conn.close()
        
        print(f"Datos cargados: {len(df)} instituciones")
        print(f"Columnas disponibles: {len(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"Error al cargar datos SQL: {e}")
        return None

def ejecutar_clustering_kmeans(df):
    """
    Ejecuta algoritmo K-means basado en el script de R
    """
    
    print("=== ALGORITMO K-MEANS ===")
    
    # Variables seleccionadas según el script R
    variables_clustering = [
        'Y1_ILA',              # Logro académico
        'Y2_TD',               # Tendencia desempeño  
        'X1_NVC',              # Vulnerabilidad contextual
        'X2_TR',               # Ruralidad
        'X4_IDD',              # Desempeño docente
        'X11_RED',             # Ratio estudiante-docente
        'X12_TOE',             # Organización escolar
        'X13_TMATRC',          # Tendencia matrícula
        'X14_NIVEL_EDUCATIVO', # Nivel educativo
        'ALTITUD_MSNM'         # Altitud
    ]
    
    # Filtrar solo variables disponibles
    variables_disponibles = [var for var in variables_clustering if var in df.columns]
    print(f"Variables disponibles para clustering: {len(variables_disponibles)}")
    for var in variables_disponibles:
        print(f"  - {var}")
    
    # Preparar datos para clustering
    datos_clustering = df[['CODIGO_MODULAR', 'NOMBRE_INSTITUCION'] + variables_disponibles].copy()
    
    # Eliminar filas con valores faltantes
    datos_clustering = datos_clustering.dropna(subset=variables_disponibles)
    print(f"Instituciones válidas para clustering: {len(datos_clustering)}")
    
    if len(datos_clustering) < 10:
        print("Error: Muy pocas instituciones para clustering")
        return None
    
    # Estandarizar variables (Z-score)
    X = datos_clustering[variables_disponibles]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Verificar estandarización
    print("Verificación estandarización:")
    print(f"  Medias ~0: {np.abs(X_scaled.mean(axis=0)).max():.3f}")
    print(f"  Std ~1: {np.abs(X_scaled.std(axis=0) - 1).max():.3f}")
    
    # Determinar K óptimo (probar K=2 a K=8)
    k_values = range(2, 9)
    silhouette_scores = []
    wcss_scores = []
    
    print("\nDeterminando K óptimo:")
    for k in k_values:
        kmeans = KMeans(n_clusters=k, random_state=123, n_init=25)
        clusters = kmeans.fit_predict(X_scaled)
        
        silhouette_avg = silhouette_score(X_scaled, clusters)
        wcss = kmeans.inertia_
        
        silhouette_scores.append(silhouette_avg)
        wcss_scores.append(wcss)
        
        print(f"  K={k}: Silhouette={silhouette_avg:.3f}, WCSS={wcss:.0f}")
    
    # Seleccionar K óptimo (mayor silhouette score)
    best_k = k_values[np.argmax(silhouette_scores)]
    best_silhouette = max(silhouette_scores)
    
    print(f"\nK óptimo seleccionado: {best_k} (Silhouette: {best_silhouette:.3f})")
    
    # Ejecutar K-means final
    kmeans_final = KMeans(n_clusters=best_k, random_state=123, n_init=25)
    clusters_final = kmeans_final.fit_predict(X_scaled)
    
    # Agregar resultados al DataFrame
    datos_clustering['CLUSTER_KMEANS'] = clusters_final + 1  # Empezar en 1, no 0
    datos_clustering['SILHOUETTE_SCORE'] = silhouette_score(X_scaled, clusters_final)
    
    # Calcular distancia al centroide para cada institución
    centroids = kmeans_final.cluster_centers_
    distances = []
    for i, row_scaled in enumerate(X_scaled):
        cluster_id = clusters_final[i]
        centroid = centroids[cluster_id]
        distance = np.linalg.norm(row_scaled - centroid)
        distances.append(distance)
    
    datos_clustering['DISTANCIA_CENTROIDE'] = distances
    
    # Crear etiquetas descriptivas de clusters
    cluster_labels = {
        1: "Tradicionales Estables",
        2: "Elite Institucional", 
        3: "Rurales Resilientes",
        4: "Emergentes Complejas",
        5: "En Desarrollo",
        6: "Especializadas",
        7: "Mixtas",
        8: "Atípicas"
    }
    
    datos_clustering['TIPOLOGIA_KMEANS'] = datos_clustering['CLUSTER_KMEANS'].map(
        lambda x: cluster_labels.get(x, f"Cluster {x}")
    )
    
    # Estadísticas por cluster
    print(f"\n=== ESTADÍSTICAS POR CLUSTER (K={best_k}) ===")
    for cluster_id in sorted(datos_clustering['CLUSTER_KMEANS'].unique()):
        cluster_data = datos_clustering[datos_clustering['CLUSTER_KMEANS'] == cluster_id]
        tipologia = cluster_data['TIPOLOGIA_KMEANS'].iloc[0]
        n_instituciones = len(cluster_data)
        ila_promedio = cluster_data['Y1_ILA'].mean() if 'Y1_ILA' in cluster_data.columns else 'N/A'
        
        print(f"Cluster {cluster_id} - {tipologia}:")
        print(f"  • {n_instituciones} instituciones ({n_instituciones/len(datos_clustering)*100:.1f}%)")
        if ila_promedio != 'N/A':
            print(f"  • ILA promedio: {ila_promedio:.3f}")
    
    return datos_clustering

def calcular_riesgo_resiliencia(df):
    """
    Calcula índices de riesgo y resiliencia basados en variables metodológicas
    """
    
    print("\n=== ALGORITMO RIESGO-RESILIENCIA ===")
    
    # Variables de vulnerabilidad (mayor valor = mayor vulnerabilidad)
    variables_vulnerabilidad = [
        'X1_NVC',    # Vulnerabilidad contextual (pobreza)
        'X2_TR',     # Ruralidad (mayor = más rural = más vulnerable)
        'X11_RED',   # Ratio estudiante/docente (mayor = más vulnerable)
    ]
    
    # Variables de capacidad (mayor valor = mayor capacidad)
    variables_capacidad = [
        'Y1_ILA',    # Logro académico
        'X4_IDD',    # Desempeño docente
        'X10_IE',    # Servicios básicos
        'X5_ED',     # Estabilidad docente
    ]
    
    # Filtrar variables disponibles
    vuln_disponibles = [var for var in variables_vulnerabilidad if var in df.columns]
    cap_disponibles = [var for var in variables_capacidad if var in df.columns]
    
    print(f"Variables vulnerabilidad disponibles: {vuln_disponibles}")
    print(f"Variables capacidad disponibles: {cap_disponibles}")
    
    # Crear copia para trabajar
    df_riesgo = df.copy()
    
    # Calcular índice de vulnerabilidad (normalizado 0-1)
    if vuln_disponibles:
        # Estandarizar variables de vulnerabilidad
        for var in vuln_disponibles:
            df_riesgo[f'{var}_norm'] = (df_riesgo[var] - df_riesgo[var].min()) / (df_riesgo[var].max() - df_riesgo[var].min())
        
        # Promedio de vulnerabilidades normalizadas
        cols_vuln_norm = [f'{var}_norm' for var in vuln_disponibles]
        df_riesgo['VULNERABILIDAD_TOTAL'] = df_riesgo[cols_vuln_norm].mean(axis=1)
    else:
        df_riesgo['VULNERABILIDAD_TOTAL'] = 0.5  # Valor neutro
    
    # Calcular índice de capacidad (normalizado 0-1)
    if cap_disponibles:
        # Estandarizar variables de capacidad
        for var in cap_disponibles:
            df_riesgo[f'{var}_norm'] = (df_riesgo[var] - df_riesgo[var].min()) / (df_riesgo[var].max() - df_riesgo[var].min())
        
        # Promedio de capacidades normalizadas
        cols_cap_norm = [f'{var}_norm' for var in cap_disponibles]
        df_riesgo['CAPACIDAD_TOTAL'] = df_riesgo[cols_cap_norm].mean(axis=1)
    else:
        df_riesgo['CAPACIDAD_TOTAL'] = 0.5  # Valor neutro
    
    # Calcular índice de riesgo (vulnerabilidad - capacidad)
    df_riesgo['RIESGO_TOTAL'] = df_riesgo['VULNERABILIDAD_TOTAL'] - df_riesgo['CAPACIDAD_TOTAL']
    
    # Calcular índice de resiliencia (capacidad - vulnerabilidad)
    df_riesgo['RESILIENCIA_TOTAL'] = df_riesgo['CAPACIDAD_TOTAL'] - df_riesgo['VULNERABILIDAD_TOTAL']
    
    # Categorizar riesgo y resiliencia
    def categorizar_riesgo(valor):
        if valor <= -0.3:
            return "Bajo Riesgo"
        elif valor <= 0.0:
            return "Riesgo Moderado"
        elif valor <= 0.3:
            return "Alto Riesgo"
        else:
            return "Muy Alto Riesgo"
    
    def categorizar_resiliencia(valor):
        if valor >= 0.3:
            return "Alta Resiliencia"
        elif valor >= 0.0:
            return "Resiliencia Moderada"
        elif valor >= -0.3:
            return "Baja Resiliencia"
        else:
            return "Muy Baja Resiliencia"
    
    df_riesgo['CATEGORIA_RIESGO'] = df_riesgo['RIESGO_TOTAL'].apply(categorizar_riesgo)
    df_riesgo['CATEGORIA_RESILIENCIA'] = df_riesgo['RESILIENCIA_TOTAL'].apply(categorizar_resiliencia)
    
    # Estadísticas
    print(f"\n=== ESTADÍSTICAS RIESGO-RESILIENCIA ===")
    print("Distribución por categoría de riesgo:")
    print(df_riesgo['CATEGORIA_RIESGO'].value_counts())
    
    print("\nDistribución por categoría de resiliencia:")
    print(df_riesgo['CATEGORIA_RESILIENCIA'].value_counts())
    
    print(f"\nEstadísticas descriptivas:")
    print(f"  Vulnerabilidad - Media: {df_riesgo['VULNERABILIDAD_TOTAL'].mean():.3f}")
    print(f"  Capacidad - Media: {df_riesgo['CAPACIDAD_TOTAL'].mean():.3f}")
    print(f"  Riesgo - Media: {df_riesgo['RIESGO_TOTAL'].mean():.3f}")
    print(f"  Resiliencia - Media: {df_riesgo['RESILIENCIA_TOTAL'].mean():.3f}")
    
    return df_riesgo[['CODIGO_MODULAR', 'VULNERABILIDAD_TOTAL', 'CAPACIDAD_TOTAL', 
                      'RIESGO_TOTAL', 'RESILIENCIA_TOTAL', 'CATEGORIA_RIESGO', 'CATEGORIA_RESILIENCIA']]

def actualizar_tabla_indices_metodologicos(clustering_results, riesgo_results, db_path):
    """
    Actualiza la tabla indices_metodologicos con los resultados de clustering y riesgo-resiliencia
    """
    
    print("\n=== ACTUALIZANDO TABLA INDICES_METODOLOGICOS ===")
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Cargar tabla actual
        df_indices = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
        print(f"Tabla actual: {len(df_indices)} registros")
        
        # Hacer merge con resultados de clustering
        if clustering_results is not None:
            df_indices = df_indices.merge(
                clustering_results[['CODIGO_MODULAR', 'CLUSTER_KMEANS', 'TIPOLOGIA_KMEANS', 
                                   'SILHOUETTE_SCORE', 'DISTANCIA_CENTROIDE']], 
                on='CODIGO_MODULAR', 
                how='left'
            )
            print(f"Clustering agregado: {clustering_results['CLUSTER_KMEANS'].notna().sum()} instituciones")
        
        # Hacer merge con resultados de riesgo-resiliencia
        if riesgo_results is not None:
            df_indices = df_indices.merge(
                riesgo_results, 
                on='CODIGO_MODULAR', 
                how='left'
            )
            print(f"Riesgo-resiliencia agregado: {riesgo_results['RIESGO_TOTAL'].notna().sum()} instituciones")
        
        # Reemplazar tabla en la base de datos
        df_indices.to_sql('indices_metodologicos', conn, if_exists='replace', index=False)
        
        # Verificar actualización
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM indices_metodologicos")
        total_registros = cursor.fetchone()[0]
        
        # Verificar nuevas columnas
        cursor.execute("PRAGMA table_info(indices_metodologicos)")
        columnas_nuevas = cursor.fetchall()
        
        print(f"Tabla actualizada exitosamente:")
        print(f"  - Total registros: {total_registros}")
        print(f"  - Total columnas: {len(columnas_nuevas)}")
        
        # Mostrar nuevas columnas agregadas
        nuevas_cols = [col[1] for col in columnas_nuevas if col[1] in [
            'CLUSTER_KMEANS', 'TIPOLOGIA_KMEANS', 'SILHOUETTE_SCORE', 'DISTANCIA_CENTROIDE',
            'VULNERABILIDAD_TOTAL', 'CAPACIDAD_TOTAL', 'RIESGO_TOTAL', 'RESILIENCIA_TOTAL',
            'CATEGORIA_RIESGO', 'CATEGORIA_RESILIENCIA'
        ]]
        
        if nuevas_cols:
            print(f"Nuevas columnas agregadas: {', '.join(nuevas_cols)}")
        
        conn.close()
        return df_indices
        
    except Exception as e:
        print(f"Error al actualizar tabla: {e}")
        return None

def main():
    """
    Función principal que ejecuta todo el proceso
    """
    
    # Cargar datos
    df = cargar_datos_desde_sql()
    if df is None:
        return
    
    # Ejecutar clustering K-means
    clustering_results = ejecutar_clustering_kmeans(df)
    
    # Ejecutar análisis de riesgo-resiliencia
    riesgo_results = calcular_riesgo_resiliencia(df)
    
    # Actualizar tabla en base de datos
    db_path = r"archivado\clustering\02 Informe Entregado\Anexo B - Base de datos SQL v5.db"
    df_actualizado = actualizar_tabla_indices_metodologicos(clustering_results, riesgo_results, db_path)
    
    if df_actualizado is not None:
        print(f"\n{'='*60}")
        print("PROCESO COMPLETADO EXITOSAMENTE")
        print("="*60)
        print(f"Base de datos actualizada con:")
        print(f"  • Resultados de clustering K-means")
        print(f"  • Índices de riesgo y resiliencia")
        print(f"  • Categorías descriptivas para dashboard")
        
        # Guardar también como CSV para verificación
        archivo_verificacion = 'indices_metodologicos_actualizado.csv'
        df_actualizado.to_csv(archivo_verificacion, index=False, encoding='utf-8')
        print(f"  • Archivo de verificación: {archivo_verificacion}")
        
        # Mostrar distribución final
        if 'CLUSTER_KMEANS' in df_actualizado.columns:
            print(f"\nDistribución final por cluster:")
            distribucion_clusters = df_actualizado['CLUSTER_KMEANS'].value_counts().sort_index()
            for cluster, cantidad in distribucion_clusters.items():
                tipologia = df_actualizado[df_actualizado['CLUSTER_KMEANS'] == cluster]['TIPOLOGIA_KMEANS'].iloc[0]
                print(f"  Cluster {cluster} ({tipologia}): {cantidad} instituciones")
        
        if 'CATEGORIA_RIESGO' in df_actualizado.columns:
            print(f"\nDistribución final por riesgo:")
            distribucion_riesgo = df_actualizado['CATEGORIA_RIESGO'].value_counts()
            for categoria, cantidad in distribucion_riesgo.items():
                print(f"  {categoria}: {cantidad} instituciones")
    
    return df_actualizado

if __name__ == "__main__":
    resultado_final = main()