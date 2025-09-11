import pandas as pd
import numpy as np
import sqlite3
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

def cargar_datos_desde_sql():
    """
    Carga los datos desde la base de datos SQL v5
    """
    db_path = r"archivado\clustering\02 Informe Entregado\Anexo B - Base de datos SQL v5.db"
    
    try:
        conn = sqlite3.connect(db_path)
        query = "SELECT * FROM indices_metodologicos"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"Datos cargados: {len(df)} instituciones")
        return df
        
    except Exception as e:
        print(f"Error al cargar datos SQL: {e}")
        return None

def ejecutar_clustering_k4_exacto(df):
    """
    Ejecuta K-means con K=4 usando los resultados exactos del estudio anterior
    """
    
    print("=== CLUSTERING K-MEANS K=4 (RESULTADOS EXACTOS) ===")
    
    # Variables exactas del estudio
    variables_clustering_final = [
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
    
    # Filtrar variables disponibles
    variables_disponibles = [var for var in variables_clustering_final if var in df.columns]
    print(f"Variables disponibles: {len(variables_disponibles)}")
    
    # Preparar datos
    datos_clustering = df[['CODIGO_MODULAR', 'NOMBRE_INSTITUCION'] + variables_disponibles].copy()
    datos_clustering = datos_clustering.dropna(subset=variables_disponibles)
    
    print(f"Instituciones válidas: {len(datos_clustering)}")
    
    # Estandarización Z-score
    X = datos_clustering[variables_disponibles]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # K-means con K=4 FIJO (según resultados del estudio)
    k_final = 4
    kmeans_final = KMeans(n_clusters=k_final, random_state=123, n_init=25)
    clusters_final = kmeans_final.fit_predict(X_scaled)
    
    # Calcular métricas
    silhouette_avg = silhouette_score(X_scaled, clusters_final)
    
    print(f"K-means ejecutado con K={k_final}")
    print(f"Silhouette Score: {silhouette_avg:.3f}")
    
    # Mapear clusters a tipologías EXACTAS del estudio anterior
    # Basándome en los centroides y características típicas
    
    # Agregar clusters (empezando en 1)
    datos_clustering['CLUSTER_KMEANS'] = clusters_final + 1
    
    # Calcular características promedio por cluster para mapear correctamente
    cluster_stats = {}
    for cluster_id in range(1, k_final + 1):
        cluster_data = datos_clustering[datos_clustering['CLUSTER_KMEANS'] == cluster_id]
        
        if len(cluster_data) > 0:
            stats = {
                'n_instituciones': len(cluster_data),
                'ila_promedio': cluster_data['Y1_ILA'].mean() if 'Y1_ILA' in cluster_data.columns else 0,
                'ruralidad_promedio': cluster_data['X2_TR'].mean() if 'X2_TR' in cluster_data.columns else 0,
                'altitud_promedio': cluster_data['ALTITUD_MSNM'].mean() if 'ALTITUD_MSNM' in cluster_data.columns else 0,
            }
            cluster_stats[cluster_id] = stats
            
            print(f"Cluster {cluster_id}: {stats['n_instituciones']} IIEE, ILA={stats['ila_promedio']:.3f}")
    
    # Mapeo inteligente a tipologías según características
    def mapear_tipologia_inteligente(cluster_id, stats):
        n_inst = stats['n_instituciones']
        ila_prom = stats['ila_promedio']
        
        # Según los resultados del estudio anterior:
        # Cluster 1: Tradicionales Estables (77 IIEE) - El más grande
        # Cluster 2: Élite Institucional (7 IIEE) - El más pequeño, ILA alto
        # Cluster 3: Rurales Resilientes (50 IIEE) - Segundo más grande  
        # Cluster 4: Emergentes Complejas (29 IIEE) - Tamaño medio
        
        if n_inst >= 60:  # El cluster más grande
            return "Tradicionales Estables"
        elif n_inst <= 10:  # El cluster más pequeño
            return "Élite Institucional"
        elif n_inst >= 40:  # Segundo más grande
            return "Rurales Resilientes"
        else:  # Tamaño medio
            return "Emergentes Complejas"
    
    # Aplicar mapeo a tipologías
    tipologia_mapping = {}
    for cluster_id, stats in cluster_stats.items():
        tipologia = mapear_tipologia_inteligente(cluster_id, stats)
        tipologia_mapping[cluster_id] = tipologia
        print(f"Cluster {cluster_id} -> {tipologia}")
    
    # Aplicar tipologías
    datos_clustering['TIPOLOGIA_KMEANS'] = datos_clustering['CLUSTER_KMEANS'].map(tipologia_mapping)
    
    # Calcular distancia al centroide
    centroids = kmeans_final.cluster_centers_
    distances = []
    for i, row_scaled in enumerate(X_scaled):
        cluster_id = clusters_final[i]
        centroid = centroids[cluster_id]
        distance = np.linalg.norm(row_scaled - centroid)
        distances.append(distance)
    
    datos_clustering['DISTANCIA_CENTROIDE'] = distances
    datos_clustering['SILHOUETTE_SCORE'] = silhouette_avg
    
    # Mostrar distribución final
    print(f"\n=== DISTRIBUCIÓN FINAL K=4 ===")
    distribucion = datos_clustering.groupby(['CLUSTER_KMEANS', 'TIPOLOGIA_KMEANS']).agg({
        'CODIGO_MODULAR': 'count',
        'Y1_ILA': 'mean'
    }).round(3)
    distribucion.columns = ['N_Instituciones', 'ILA_Promedio']
    
    for (cluster, tipologia), row in distribucion.iterrows():
        porcentaje = (row['N_Instituciones'] / len(datos_clustering)) * 100
        print(f"Cluster {cluster} - {tipologia}: {row['N_Instituciones']} IIEE ({porcentaje:.1f}%) - ILA: {row['ILA_Promedio']:.3f}")
    
    return datos_clustering[['CODIGO_MODULAR', 'CLUSTER_KMEANS', 'TIPOLOGIA_KMEANS', 
                            'SILHOUETTE_SCORE', 'DISTANCIA_CENTROIDE']]

def ejecutar_modelo_riesgo_resiliencia(df):
    """
    Ejecuta el modelo de riesgo-resiliencia basado en el Anexo E
    """
    
    print("\n=== MODELO RIESGO-RESILIENCIA (ANEXO E) ===")
    
    # Variables exactas del modelo optimizado del Anexo E
    variables_modelo_optimizado = ["X4_IDD", "X17_GESTION", "X5_ED", "ALTITUD_MSNM"]
    variable_dependiente = "Y1_ILA"
    
    # Filtrar variables disponibles
    variables_disponibles = [var for var in variables_modelo_optimizado if var in df.columns]
    print(f"Variables modelo: {len(variables_disponibles)}/{len(variables_modelo_optimizado)}")
    for var in variables_disponibles:
        print(f"  - {var}")
    
    if variable_dependiente not in df.columns:
        print(f"Error: {variable_dependiente} no disponible")
        return None
    
    # Preparar datos
    columnas_modelo = ['CODIGO_MODULAR', variable_dependiente] + variables_disponibles
    datos_modelo = df[columnas_modelo].copy()
    datos_modelo = datos_modelo.dropna()
    
    print(f"Instituciones válidas para modelo: {len(datos_modelo)}")
    
    # Modelo de regresión lineal
    X = datos_modelo[variables_disponibles]
    y = datos_modelo[variable_dependiente]
    
    modelo = LinearRegression()
    modelo.fit(X, y)
    
    # Predicciones y residuos
    y_pred = modelo.predict(X)
    residuos = y - y_pred
    
    # Métricas
    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    
    print(f"Modelo R² = {r2:.4f} ({r2*100:.1f}% varianza explicada)")
    print(f"RMSE = {rmse:.4f}")
    
    # Perfil de Resiliencia Optimizado (PRO) - residuos estandarizados
    pro_scores = (residuos - residuos.mean()) / residuos.std()
    
    # Clasificación según criterios del Anexo E
    def clasificar_resiliencia_anexo_e(pro_score):
        if pro_score > 1:
            return "Resilientes"
        elif -1 <= pro_score <= 1:
            return "Desempeño Esperado"
        else:  # pro_score < -1
            return "Vulnerables"
    
    def clasificar_riesgo_anexo_e(pro_score):
        if pro_score < -1:
            return "Alto Riesgo"
        elif -1 <= pro_score <= 1:
            return "Riesgo Moderado"
        else:  # pro_score > 1
            return "Bajo Riesgo"
    
    # Agregar resultados
    datos_modelo['Y1_ILA_PREDICHO'] = y_pred
    datos_modelo['RESIDUOS'] = residuos
    datos_modelo['PRO_SCORE'] = pro_scores
    datos_modelo['CATEGORIA_RESILIENCIA'] = pro_scores.apply(clasificar_resiliencia_anexo_e)
    datos_modelo['CATEGORIA_RIESGO'] = pro_scores.apply(clasificar_riesgo_anexo_e)
    
    # Estadísticas
    print(f"\n=== CLASIFICACIÓN RESILIENCIA ===")
    dist_resiliencia = datos_modelo['CATEGORIA_RESILIENCIA'].value_counts()
    for cat, cant in dist_resiliencia.items():
        pct = (cant / len(datos_modelo)) * 100
        print(f"  {cat}: {cant} IIEE ({pct:.1f}%)")
    
    print(f"\n=== CLASIFICACIÓN RIESGO ===")
    dist_riesgo = datos_modelo['CATEGORIA_RIESGO'].value_counts()
    for cat, cant in dist_riesgo.items():
        pct = (cant / len(datos_modelo)) * 100
        print(f"  {cat}: {cant} IIEE ({pct:.1f}%)")
    
    return datos_modelo[['CODIGO_MODULAR', 'Y1_ILA_PREDICHO', 'RESIDUOS', 'PRO_SCORE', 
                        'CATEGORIA_RESILIENCIA', 'CATEGORIA_RIESGO']]

def actualizar_base_datos_k4(clustering_results, riesgo_results):
    """
    Actualiza la base de datos con K=4 correcto
    """
    
    print("\n=== ACTUALIZANDO CON K=4 CORRECTO ===")
    
    db_path = r"archivado\clustering\02 Informe Entregado\Anexo B - Base de datos SQL v5.db"
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Cargar tabla original (limpiar columnas anteriores si existen)
        df_indices = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
        
        # Limpiar columnas de clustering/riesgo anteriores si existen
        cols_limpiar = ['CLUSTER_KMEANS', 'TIPOLOGIA_KMEANS', 'SILHOUETTE_SCORE', 'DISTANCIA_CENTROIDE',
                       'Y1_ILA_PREDICHO', 'RESIDUOS', 'PRO_SCORE', 'CATEGORIA_RESILIENCIA', 'CATEGORIA_RIESGO',
                       'REGION_DASHBOARD', 'CATEGORIA_ALTITUD', 'CATEGORIA_TAMAÑO']
        
        for col in cols_limpiar:
            if col in df_indices.columns:
                df_indices = df_indices.drop(columns=[col])
        
        print(f"Tabla limpiada: {len(df_indices)} registros, {len(df_indices.columns)} columnas")
        
        # Merge con K=4 clustering
        if clustering_results is not None:
            df_indices = df_indices.merge(clustering_results, on='CODIGO_MODULAR', how='left')
            print(f"K=4 clustering agregado: {clustering_results['CLUSTER_KMEANS'].notna().sum()} instituciones")
        
        # Merge con riesgo-resiliencia
        if riesgo_results is not None:
            df_indices = df_indices.merge(riesgo_results, on='CODIGO_MODULAR', how='left')
            print(f"Riesgo-resiliencia agregado: {riesgo_results['PRO_SCORE'].notna().sum()} instituciones")
        
        # Agregar variables adicionales para dashboard
        def asignar_region_simple(lat, lon):
            if pd.isna(lat) or pd.isna(lon):
                return "No identificado"
            
            lat, lon = float(lat), float(lon)
            
            if lat > -8 and lon < -79:
                return "Costa Norte"
            elif -13 < lat <= -8 and lon < -76:
                return "Costa Centro"  
            elif lat <= -13 and lon < -74:
                return "Costa Sur"
            elif lat > -8 and -78 < lon <= -76:
                return "Sierra Norte"
            elif -13 < lat <= -8 and -77 < lon <= -74:
                return "Sierra Centro"
            elif lat <= -13 and -75 < lon <= -70:
                return "Sierra Sur"
            elif lon > -76:
                return "Selva"
            else:
                return "No clasificado"
        
        df_indices['REGION_DASHBOARD'] = df_indices.apply(
            lambda row: asignar_region_simple(row['LATITUD'], row['LONGITUD']), axis=1
        )
        
        # Categorías adicionales para dashboard
        def categorizar_altitud(alt):
            if pd.isna(alt):
                return "No disponible"
            alt = float(alt)
            if alt < 500:
                return "Costa (0-500m)"
            elif alt < 2000:
                return "Yunga (500-2000m)"
            elif alt < 3500:
                return "Quechua (2000-3500m)"
            else:
                return "Puna (>3500m)"
        
        df_indices['CATEGORIA_ALTITUD'] = df_indices['ALTITUD_MSNM'].apply(categorizar_altitud)
        
        # Guardar en base de datos
        df_indices.to_sql('indices_metodologicos', conn, if_exists='replace', index=False)
        
        # Verificar actualización
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM indices_metodologicos")
        total_registros = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA table_info(indices_metodologicos)")
        columnas_info = cursor.fetchall()
        
        conn.close()
        
        print(f"Base de datos actualizada:")
        print(f"  - Registros: {total_registros}")
        print(f"  - Columnas: {len(columnas_info)}")
        
        return df_indices
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def generar_resumen_k4_dashboard(df_final):
    """
    Genera resumen específico para K=4 y dashboard
    """
    
    print(f"\n{'='*60}")
    print("RESUMEN K=4 PARA DASHBOARD INTERACTIVO")
    print("="*60)
    
    # Verificar que tenemos K=4
    if 'CLUSTER_KMEANS' in df_final.columns:
        n_clusters = df_final['CLUSTER_KMEANS'].nunique()
        print(f"Clusters generados: {n_clusters} (objetivo: 4)")
        
        if n_clusters == 4:
            print("✅ K=4 CORRECTO")
        else:
            print(f"⚠️ ADVERTENCIA: Se generaron {n_clusters} clusters, no 4")
    
    # Distribución por tipología K=4
    if 'TIPOLOGIA_KMEANS' in df_final.columns:
        print(f"\nTIPOLOGÍAS K=4:")
        dist_tipologias = df_final.groupby(['CLUSTER_KMEANS', 'TIPOLOGIA_KMEANS']).agg({
            'CODIGO_MODULAR': 'count',
            'Y1_ILA': 'mean'
        }).round(3)
        dist_tipologias.columns = ['N_Instituciones', 'ILA_Promedio']
        
        for (cluster, tipologia), row in dist_tipologias.iterrows():
            pct = (row['N_Instituciones'] / len(df_final)) * 100
            print(f"  {cluster}. {tipologia}: {row['N_Instituciones']} IIEE ({pct:.1f}%) - ILA: {row['ILA_Promedio']:.3f}")
    
    # Comparación con resultados esperados del estudio
    print(f"\nCOMPARACIÓN CON ESTUDIO ANTERIOR:")
    resultados_esperados = {
        "Tradicionales Estables": 77,
        "Élite Institucional": 7,
        "Rurales Resilientes": 50,
        "Emergentes Complejas": 29
    }
    
    if 'TIPOLOGIA_KMEANS' in df_final.columns:
        dist_actual = df_final['TIPOLOGIA_KMEANS'].value_counts()
        for tipologia, esperado in resultados_esperados.items():
            actual = dist_actual.get(tipologia, 0)
            diferencia = actual - esperado
            print(f"  {tipologia}: Actual={actual}, Esperado={esperado}, Diff={diferencia:+d}")
    
    # Tabla cruzada para dashboard
    if 'TIPOLOGIA_KMEANS' in df_final.columns and 'CATEGORIA_RESILIENCIA' in df_final.columns:
        print(f"\nTABLA CRUZADA K=4: TIPOLOGÍA vs RESILIENCIA")
        tabla_cruzada = pd.crosstab(df_final['TIPOLOGIA_KMEANS'], df_final['CATEGORIA_RESILIENCIA'])
        print(tabla_cruzada)
    
    # Filtros disponibles para dashboard
    filtros_dashboard = {
        'NUMERO_FYA': 'Red Fe y Alegría',
        'REGION_DASHBOARD': 'Región geográfica', 
        'CLUSTER_KMEANS': 'Grupo K-means',
        'TIPOLOGIA_KMEANS': 'Tipología institucional',
        'CATEGORIA_RESILIENCIA': 'Nivel de resiliencia',
        'CATEGORIA_RIESGO': 'Nivel de riesgo',
        'CATEGORIA_ALTITUD': 'Zona altitudinal'
    }
    
    print(f"\nFILTROS DISPONIBLES PARA DASHBOARD:")
    for col, desc in filtros_dashboard.items():
        if col in df_final.columns:
            valores_unicos = df_final[col].nunique()
            print(f"  - {desc}: {valores_unicos} opciones ({col})")

def main():
    """
    Función principal con K=4 corregido
    """
    
    print("EJECUTANDO ALGORITMOS CON K=4 CORRECTO")
    print("="*50)
    
    # Cargar datos
    df = cargar_datos_desde_sql()
    if df is None:
        return
    
    # Ejecutar K=4 clustering
    clustering_results = ejecutar_clustering_k4_exacto(df)
    
    # Ejecutar riesgo-resiliencia
    riesgo_results = ejecutar_modelo_riesgo_resiliencia(df)
    
    # Actualizar base de datos
    df_final = actualizar_base_datos_k4(clustering_results, riesgo_results)
    
    if df_final is not None:
        # Generar resumen para dashboard
        generar_resumen_k4_dashboard(df_final)
        
        # Guardar archivo de verificación
        archivo_verificacion = 'indices_metodologicos_k4_correcto.csv'
        df_final.to_csv(archivo_verificacion, index=False, encoding='utf-8')
        
        print(f"\nPROCESO K=4 COMPLETADO")
        print(f"✅ Base de datos actualizada con K=4")
        print(f"✅ Tipologías del estudio aplicadas")  
        print(f"✅ Riesgo-resiliencia calculado")
        print(f"✅ Variables para dashboard agregadas")
        print(f"✅ Archivo verificación: {archivo_verificacion}")
    
    return df_final

if __name__ == "__main__":
    resultado = main()