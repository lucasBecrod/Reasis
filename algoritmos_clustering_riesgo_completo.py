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

def ejecutar_clustering_kmeans(df):
    """
    Ejecuta algoritmo K-means basado exactamente en el script de R (Anexo C)
    """
    
    print("=== ALGORITMO K-MEANS (BASADO EN ANEXO C) ===")
    
    # Variables exactas del script R
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
    print(f"Variables disponibles: {len(variables_disponibles)}/{len(variables_clustering_final)}")
    for var in variables_disponibles:
        print(f"  - {var}")
    
    # Preparar datos
    datos_clustering = df[['CODIGO_MODULAR', 'NOMBRE_INSTITUCION'] + variables_disponibles].copy()
    datos_clustering = datos_clustering.dropna(subset=variables_disponibles)
    
    print(f"Instituciones válidas: {len(datos_clustering)}")
    
    if len(datos_clustering) < 10:
        print("Error: Muy pocas instituciones para clustering")
        return None
    
    # Estandarización Z-score (igual que en R)
    X = datos_clustering[variables_disponibles]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    print("Verificación estandarización Z-score:")
    print(f"  Medias ~0: {np.abs(X_scaled.mean(axis=0)).max():.6f}")
    print(f"  Std ~1: {np.abs(X_scaled.std(axis=0) - 1).max():.6f}")
    
    # Determinar K óptimo (método silhouette, igual que R)
    k_values = range(2, 11)  # K=2 a K=10 como en R
    silhouette_scores = []
    wcss_scores = []
    
    print("\nAnálisis K óptimo (método silhouette):")
    for k in k_values:
        kmeans = KMeans(n_clusters=k, random_state=123, n_init=25)  # Mismo random_state que R
        clusters = kmeans.fit_predict(X_scaled)
        
        silhouette_avg = silhouette_score(X_scaled, clusters)
        wcss = kmeans.inertia_
        
        silhouette_scores.append(silhouette_avg)
        wcss_scores.append(wcss)
        
        print(f"  K={k}: Silhouette={silhouette_avg:.3f}, WCSS={wcss:.0f}")
    
    # Seleccionar K óptimo (mayor silhouette)
    best_k = k_values[np.argmax(silhouette_scores)]
    best_silhouette = max(silhouette_scores)
    
    print(f"\nK óptimo: {best_k} (Silhouette: {best_silhouette:.3f})")
    
    # K-means final
    kmeans_final = KMeans(n_clusters=best_k, random_state=123, n_init=25)
    clusters_final = kmeans_final.fit_predict(X_scaled)
    
    # Agregar resultados
    datos_clustering['CLUSTER_KMEANS'] = clusters_final + 1  # Empezar en 1
    datos_clustering['SILHOUETTE_SCORE'] = best_silhouette
    
    # Calcular distancia al centroide
    centroids = kmeans_final.cluster_centers_
    distances = []
    for i, row_scaled in enumerate(X_scaled):
        cluster_id = clusters_final[i]
        centroid = centroids[cluster_id]
        distance = np.linalg.norm(row_scaled - centroid)
        distances.append(distance)
    
    datos_clustering['DISTANCIA_CENTROIDE'] = distances
    
    # Etiquetas temáticas (del script R)
    tipologias_kmeans = {
        1: "Tradicionales Estables",
        2: "Elite Institucional", 
        3: "Rurales Resilientes",
        4: "Emergentes Complejas",
        5: "En Desarrollo",
        6: "Especializadas"
    }
    
    datos_clustering['TIPOLOGIA_KMEANS'] = datos_clustering['CLUSTER_KMEANS'].map(
        lambda x: tipologias_kmeans.get(x, f"Cluster {x}")
    )
    
    # Estadísticas por cluster
    print(f"\n=== RESULTADOS K-MEANS (K={best_k}) ===")
    for cluster_id in sorted(datos_clustering['CLUSTER_KMEANS'].unique()):
        cluster_data = datos_clustering[datos_clustering['CLUSTER_KMEANS'] == cluster_id]
        tipologia = cluster_data['TIPOLOGIA_KMEANS'].iloc[0]
        n_instituciones = len(cluster_data)
        
        print(f"Cluster {cluster_id} - {tipologia}: {n_instituciones} IIEE ({n_instituciones/len(datos_clustering)*100:.1f}%)")
        
        if 'Y1_ILA' in cluster_data.columns:
            ila_promedio = cluster_data['Y1_ILA'].mean()
            print(f"  • ILA promedio: {ila_promedio:.3f}")
    
    return datos_clustering[['CODIGO_MODULAR', 'CLUSTER_KMEANS', 'TIPOLOGIA_KMEANS', 
                            'SILHOUETTE_SCORE', 'DISTANCIA_CENTROIDE']]

def ejecutar_modelo_riesgo_resiliencia(df):
    """
    Ejecuta el modelo de riesgo-resiliencia basado exactamente en el Anexo E
    """
    
    print("\n=== MODELO RIESGO-RESILIENCIA (BASADO EN ANEXO E) ===")
    
    # Variables del modelo optimizado según Anexo E
    variables_modelo_optimizado = ["X4_IDD", "X17_GESTION", "X5_ED", "ALTITUD_MSNM"]
    variable_dependiente = "Y1_ILA"
    
    # Filtrar variables disponibles
    variables_disponibles = [var for var in variables_modelo_optimizado if var in df.columns]
    print(f"Variables modelo disponibles: {len(variables_disponibles)}/{len(variables_modelo_optimizado)}")
    for var in variables_disponibles:
        print(f"  - {var}")
    
    if variable_dependiente not in df.columns:
        print(f"Error: Variable dependiente {variable_dependiente} no disponible")
        return None
    
    # Preparar datos para modelo
    columnas_modelo = ['CODIGO_MODULAR', 'NOMBRE_INSTITUCION', variable_dependiente] + variables_disponibles
    datos_modelo = df[columnas_modelo].copy()
    datos_modelo = datos_modelo.dropna()
    
    print(f"Instituciones válidas para modelo: {len(datos_modelo)}")
    
    if len(datos_modelo) < 10:
        print("Error: Muy pocas instituciones para modelo de regresión")
        return None
    
    # Preparar matrices X e y
    X = datos_modelo[variables_disponibles]
    y = datos_modelo[variable_dependiente]
    
    # Ajustar modelo de regresión lineal
    modelo = LinearRegression()
    modelo.fit(X, y)
    
    # Predicciones y residuos
    y_pred = modelo.predict(X)
    residuos = y - y_pred
    
    # Métricas del modelo
    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    
    print(f"\nMétricas del modelo:")
    print(f"  R² = {r2:.4f} ({r2*100:.1f}% varianza explicada)")
    print(f"  RMSE = {rmse:.4f}")
    
    # Calcular Perfil de Resiliencia Optimizado (PRO)
    # PRO = residuos estandarizados (como en Anexo E)
    pro_scores = (residuos - residuos.mean()) / residuos.std()
    
    # Clasificación por resiliencia (criterios del Anexo E)
    def clasificar_resiliencia(pro_score):
        if pro_score > 1:
            return "Resilientes"
        elif -1 <= pro_score <= 1:
            return "Desempeño Esperado"
        else:  # pro_score < -1
            return "Vulnerables"
    
    # Agregar resultados
    datos_modelo['Y1_ILA_PREDICHO'] = y_pred
    datos_modelo['RESIDUOS'] = residuos
    datos_modelo['PRO_SCORE'] = pro_scores
    datos_modelo['CATEGORIA_RESILIENCIA'] = pro_scores.apply(clasificar_resiliencia)
    
    # Clasificación adicional de riesgo (inverso de resiliencia)
    def clasificar_riesgo(pro_score):
        if pro_score < -1:
            return "Alto Riesgo"
        elif -1 <= pro_score <= 1:
            return "Riesgo Moderado"
        else:  # pro_score > 1
            return "Bajo Riesgo"
    
    datos_modelo['CATEGORIA_RIESGO'] = pro_scores.apply(clasificar_riesgo)
    
    # Estadísticas por categoría
    print(f"\n=== CLASIFICACIÓN POR RESILIENCIA ===")
    distribucion_resiliencia = datos_modelo['CATEGORIA_RESILIENCIA'].value_counts()
    for categoria, cantidad in distribucion_resiliencia.items():
        porcentaje = (cantidad / len(datos_modelo)) * 100
        print(f"  {categoria}: {cantidad} IIEE ({porcentaje:.1f}%)")
    
    print(f"\n=== CLASIFICACIÓN POR RIESGO ===")
    distribucion_riesgo = datos_modelo['CATEGORIA_RIESGO'].value_counts()
    for categoria, cantidad in distribucion_riesgo.items():
        porcentaje = (cantidad / len(datos_modelo)) * 100
        print(f"  {categoria}: {cantidad} IIEE ({porcentaje:.1f}%)")
    
    # Análisis por grupo
    print(f"\n=== ANÁLISIS POR GRUPO ===")
    for categoria in datos_modelo['CATEGORIA_RESILIENCIA'].unique():
        grupo = datos_modelo[datos_modelo['CATEGORIA_RESILIENCIA'] == categoria]
        ila_real = grupo['Y1_ILA'].mean()
        ila_esperado = grupo['Y1_ILA_PREDICHO'].mean()
        pro_promedio = grupo['PRO_SCORE'].mean()
        
        print(f"\n{categoria} ({len(grupo)} instituciones):")
        print(f"  • ILA Real: {ila_real:.3f}")
        print(f"  • ILA Esperado: {ila_esperado:.3f}")
        print(f"  • PRO Promedio: {pro_promedio:.3f}")
        print(f"  • Brecha: {ila_real - ila_esperado:.3f}")
    
    return datos_modelo[['CODIGO_MODULAR', 'Y1_ILA_PREDICHO', 'RESIDUOS', 'PRO_SCORE', 
                        'CATEGORIA_RESILIENCIA', 'CATEGORIA_RIESGO']]

def actualizar_tabla_indices_metodologicos(clustering_results, riesgo_results):
    """
    Actualiza la tabla indices_metodologicos con ambos resultados
    """
    
    print("\n=== ACTUALIZANDO TABLA INDICES_METODOLOGICOS ===")
    
    db_path = r"archivado\clustering\02 Informe Entregado\Anexo B - Base de datos SQL v5.db"
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Cargar tabla actual
        df_indices = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
        print(f"Tabla actual: {len(df_indices)} registros, {len(df_indices.columns)} columnas")
        
        # Merge con resultados de clustering
        if clustering_results is not None:
            df_indices = df_indices.merge(clustering_results, on='CODIGO_MODULAR', how='left')
            clustering_count = df_indices['CLUSTER_KMEANS'].notna().sum()
            print(f"Clustering K-means agregado: {clustering_count} instituciones")
        
        # Merge con resultados de riesgo-resiliencia
        if riesgo_results is not None:
            df_indices = df_indices.merge(riesgo_results, on='CODIGO_MODULAR', how='left')
            riesgo_count = df_indices['PRO_SCORE'].notna().sum()
            print(f"Riesgo-resiliencia agregado: {riesgo_count} instituciones")
        
        # Agregar columnas calculadas adicionales para dashboard
        
        # 1. Región geográfica simplificada (para filtros)
        def asignar_region_dashboard(lat, lon):
            if pd.isna(lat) or pd.isna(lon):
                return "No identificado"
            
            lat, lon = float(lat), float(lon)
            
            # Lógica simplificada para dashboard
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
            lambda row: asignar_region_dashboard(row['LATITUD'], row['LONGITUD']), axis=1
        )
        
        # 2. Nivel de altitud categorizado
        def categorizar_altitud(altitud):
            if pd.isna(altitud):
                return "No disponible"
            altitud = float(altitud)
            if altitud < 500:
                return "Costa (0-500m)"
            elif altitud < 2000:
                return "Yunga (500-2000m)"
            elif altitud < 3500:
                return "Quechua (2000-3500m)"
            elif altitud < 4000:
                return "Suni (3500-4000m)"
            else:
                return "Puna (>4000m)"
        
        df_indices['CATEGORIA_ALTITUD'] = df_indices['ALTITUD_MSNM'].apply(categorizar_altitud)
        
        # 3. Tamaño institucional
        def categorizar_tamaño(red_ratio):
            if pd.isna(red_ratio):
                return "No disponible"
            red_ratio = float(red_ratio)
            if red_ratio <= 10:
                return "Pequeña (≤10 est/doc)"
            elif red_ratio <= 20:
                return "Mediana (11-20 est/doc)"
            elif red_ratio <= 30:
                return "Grande (21-30 est/doc)"
            else:
                return "Muy Grande (>30 est/doc)"
        
        df_indices['CATEGORIA_TAMAÑO'] = df_indices['X11_RED'].apply(categorizar_tamaño)
        
        # Reemplazar tabla en base de datos
        df_indices.to_sql('indices_metodologicos', conn, if_exists='replace', index=False)
        
        # Verificar actualización
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM indices_metodologicos")
        total_registros = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA table_info(indices_metodologicos)")
        columnas_info = cursor.fetchall()
        total_columnas = len(columnas_info)
        
        print(f"\nTabla actualizada exitosamente:")
        print(f"  - Registros: {total_registros}")
        print(f"  - Columnas totales: {total_columnas}")
        
        # Mostrar nuevas columnas agregadas
        nuevas_cols = [col[1] for col in columnas_info if col[1] in [
            'CLUSTER_KMEANS', 'TIPOLOGIA_KMEANS', 'SILHOUETTE_SCORE', 'DISTANCIA_CENTROIDE',
            'Y1_ILA_PREDICHO', 'RESIDUOS', 'PRO_SCORE', 'CATEGORIA_RESILIENCIA', 'CATEGORIA_RIESGO',
            'REGION_DASHBOARD', 'CATEGORIA_ALTITUD', 'CATEGORIA_TAMAÑO'
        ]]
        
        if nuevas_cols:
            print(f"Nuevas columnas agregadas: {len(nuevas_cols)}")
            for col in nuevas_cols:
                print(f"    - {col}")
        
        conn.close()
        
        # Guardar CSV de verificación
        archivo_verificacion = 'indices_metodologicos_con_clustering_riesgo.csv'
        df_indices.to_csv(archivo_verificacion, index=False, encoding='utf-8')
        print(f"\nArchivo de verificación guardado: {archivo_verificacion}")
        
        return df_indices
        
    except Exception as e:
        print(f"Error al actualizar tabla: {e}")
        return None

def generar_resumen_dashboard(df_final):
    """
    Genera resumen de datos para dashboard interactivo
    """
    
    print(f"\n{'='*60}")
    print("RESUMEN PARA DASHBOARD INTERACTIVO")
    print("="*60)
    
    print(f"Total instituciones: {len(df_final)}")
    
    # Distribución por clustering
    if 'CLUSTER_KMEANS' in df_final.columns:
        print(f"\nDISTRIBUCIÓN POR TIPOLOGÍA K-MEANS:")
        dist_clusters = df_final.groupby(['CLUSTER_KMEANS', 'TIPOLOGIA_KMEANS']).size().reset_index(name='cantidad')
        for _, row in dist_clusters.iterrows():
            porcentaje = (row['cantidad'] / len(df_final)) * 100
            print(f"  Cluster {int(row['CLUSTER_KMEANS'])} - {row['TIPOLOGIA_KMEANS']}: {row['cantidad']} IIEE ({porcentaje:.1f}%)")
    
    # Distribución por riesgo-resiliencia
    if 'CATEGORIA_RESILIENCIA' in df_final.columns:
        print(f"\nDISTRIBUCIÓN POR RESILIENCIA:")
        dist_resiliencia = df_final['CATEGORIA_RESILIENCIA'].value_counts()
        for categoria, cantidad in dist_resiliencia.items():
            porcentaje = (cantidad / len(df_final)) * 100
            print(f"  {categoria}: {cantidad} IIEE ({porcentaje:.1f}%)")
    
    if 'CATEGORIA_RIESGO' in df_final.columns:
        print(f"\nDISTRIBUCIÓN POR RIESGO:")
        dist_riesgo = df_final['CATEGORIA_RIESGO'].value_counts()
        for categoria, cantidad in dist_riesgo.items():
            porcentaje = (cantidad / len(df_final)) * 100
            print(f"  {categoria}: {cantidad} IIEE ({porcentaje:.1f}%)")
    
    # Distribución por región
    if 'REGION_DASHBOARD' in df_final.columns:
        print(f"\nDISTRIBUCIÓN POR REGIÓN:")
        dist_region = df_final['REGION_DASHBOARD'].value_counts()
        for region, cantidad in dist_region.items():
            porcentaje = (cantidad / len(df_final)) * 100
            print(f"  {region}: {cantidad} IIEE ({porcentaje:.1f}%)")
    
    # Crear tabla cruzada: Clustering vs Resiliencia
    if 'TIPOLOGIA_KMEANS' in df_final.columns and 'CATEGORIA_RESILIENCIA' in df_final.columns:
        print(f"\nTABLA CRUZADA: TIPOLOGÍA vs RESILIENCIA")
        tabla_cruzada = pd.crosstab(df_final['TIPOLOGIA_KMEANS'], df_final['CATEGORIA_RESILIENCIA'], margins=True)
        print(tabla_cruzada)
    
    print(f"\n{'='*60}")
    print("COLUMNAS DISPONIBLES PARA DASHBOARD:")
    print("="*60)
    columnas_dashboard = [col for col in df_final.columns if any(keyword in col for keyword in [
        'CLUSTER', 'TIPOLOGIA', 'CATEGORIA', 'REGION', 'NUMERO_FYA', 'ALTITUD'
    ])]
    
    for col in sorted(columnas_dashboard):
        valores_unicos = df_final[col].nunique() if col in df_final.columns else 0
        print(f"  - {col}: {valores_unicos} valores únicos")

def main():
    """
    Función principal
    """
    
    print("INICIANDO CÁLCULO DE CLUSTERING Y RIESGO-RESILIENCIA")
    print("="*70)
    
    # Cargar datos
    df = cargar_datos_desde_sql()
    if df is None:
        return
    
    # Ejecutar clustering K-means
    clustering_results = ejecutar_clustering_kmeans(df)
    
    # Ejecutar modelo riesgo-resiliencia  
    riesgo_results = ejecutar_modelo_riesgo_resiliencia(df)
    
    # Actualizar base de datos
    df_final = actualizar_tabla_indices_metodologicos(clustering_results, riesgo_results)
    
    # Generar resumen para dashboard
    if df_final is not None:
        generar_resumen_dashboard(df_final)
        
        print(f"\n🎯 PROCESO COMPLETADO EXITOSAMENTE")
        print(f"La tabla 'indices_metodologicos' ahora incluye:")
        print(f"  ✅ Grupos de clustering K-means con etiquetas")
        print(f"  ✅ Categorías de riesgo y resiliencia")
        print(f"  ✅ Variables adicionales para dashboard")
        print(f"  ✅ Listo para crear dashboard interactivo")
    
    return df_final

if __name__ == "__main__":
    resultado = main()