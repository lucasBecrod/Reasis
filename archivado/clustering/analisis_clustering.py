import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings

# --- 1. CONFIGURACIÓN CENTRALIZADA ---
# Ignorar advertencias futuras de scikit-learn sobre n_init para una salida más limpia
warnings.filterwarnings(
    "ignore",
    message="The default value of `n_init` will change from 10 to 'auto' in 1.4.",
    category=FutureWarning
)

# --- Parámetros del Análisis ---
# Ruta al archivo CSV de entrada
FILE_PATH = Path('01 Analisis Excel/reasis_database_v5_final.csv')

# Directorio para guardar los gráficos y resultados
OUTPUT_DIR = Path('analisis_clustering_output')

# Lista de variables a utilizar para el clustering
CLUSTERING_VARS = [
    'Y1_ILA', 'Y2_TD', 'X1_NVC', 'X2_TR', 'X4_IDD', 'X11_RED', 
    'X12_TOE', 'X13_TMATRC', 'X14_NIVEL_EDUCATIVO', 'ALTITUD_MSNM'
]

# Número óptimo de clusters (determinado por el análisis del codo/silueta)
# El análisis previo sugiere que 4 es una buena opción.
OPTIMAL_K = 4

# --- 2. FUNCIONES DEL ANÁLISIS ---

def load_and_inspect_data(file_path: Path) -> pd.DataFrame:
    """Carga y verifica la integridad del dataset."""
    print(f"--- Paso 1: Cargando datos de '{file_path}' ---")
    if not file_path.exists():
        raise FileNotFoundError(f"El archivo no se encontró en: {file_path}")
    
    df = pd.read_csv(file_path, sep=';')
    print(f"Forma del dataset: {df.shape}")
    print("Verificación de valores faltantes por columna:")
    print(df.isna().sum().to_string())
    
    if df.isna().sum().sum() > 0:
        print("\n¡Atención! Se encontraron valores faltantes. Considera una estrategia de imputación.")
    else:
        print("✅ No se encontraron valores faltantes.")
    
    return df

def plot_correlation_heatmap(df: pd.DataFrame, columns: list, output_dir: Path):
    """Genera y guarda un heatmap de correlaciones."""
    print("\n--- Paso 2: Generando Heatmap de Correlaciones ---")
    corr_matrix = df[columns].corr()
    
    plt.figure(figsize=(12, 10))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, fmt=".2f")
    plt.title('Heatmap de Correlaciones de Variables para Clustering')
    plt.tight_layout()
    
    save_path = output_dir / 'heatmap_correlaciones.png'
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"✅ Heatmap de correlaciones guardado en: {save_path}")

def find_optimal_k(scaled_data: pd.DataFrame, max_k: int, output_dir: Path):
    """Calcula y grafica los métodos del codo y la silueta para encontrar K."""
    print("\n--- Paso 3: Determinando el número óptimo de clusters (K) ---")
    wcss = []
    sil_scores = []
    k_range = range(2, max_k + 1)
    
    for k in k_range:
        kmeans = KMeans(n_clusters=k, n_init=10, random_state=123)
        kmeans.fit(scaled_data)
        wcss.append(kmeans.inertia_)
        sil_scores.append(silhouette_score(scaled_data, kmeans.labels_))

    # Gráfico del Codo
    plt.figure(figsize=(8, 5))
    plt.plot(k_range, wcss, marker='o', linestyle='--')
    plt.title('Método del Codo para Determinar K Óptimo')
    plt.xlabel('Número de Clusters (K)')
    plt.ylabel('WCSS (Inercia)')
    plt.grid(True)
    codo_path = output_dir / 'metodo_codo.png'
    plt.savefig(codo_path, dpi=150)
    plt.close()
    print(f"✅ Gráfico del codo guardado en: {codo_path}")

    # Gráfico de la Silueta
    plt.figure(figsize=(8, 5))
    plt.plot(k_range, sil_scores, marker='o', linestyle='--')
    plt.title('Puntajes de Silueta para Determinar K Óptimo')
    plt.xlabel('Número de Clusters (K)')
    plt.ylabel('Silhouette Score')
    plt.grid(True)
    sil_path = output_dir / 'silhouette_scores.png'
    plt.savefig(sil_path, dpi=150)
    plt.close()
    print(f"✅ Gráfico de silueta guardado en: {sil_path}")
    
    best_k_sil = k_range[np.argmax(sil_scores)]
    print(f"💡 El mejor K según el puntaje de silueta es: {best_k_sil}")

def run_and_analyze_clustering(df: pd.DataFrame, scaled_data: pd.DataFrame, scaler: StandardScaler, k: int, columns: list, output_dir: Path):
    """Ejecuta K-Means con el K óptimo y analiza los resultados."""
    print(f"\n--- Paso 4: Ejecutando Clustering con K={k} ---")
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=123)
    df['cluster'] = kmeans.fit_predict(scaled_data)
    
    print("\nTamaño de cada cluster:")
    print(df['cluster'].value_counts().sort_index())

    # Centroides en escala original (más interpretables)
    centroids_scaled = kmeans.cluster_centers_
    centroids_original = scaler.inverse_transform(centroids_scaled)
    centroids_df = pd.DataFrame(centroids_original, columns=columns)
    print("\nCentroides de los clusters (en escala original de las variables):")
    print(centroids_df.round(2))
    centroids_df.to_csv(output_dir / 'centroides_clusters.csv', index_label='cluster', sep=';', decimal='.')
    print(f"✅ Centroides guardados en: {output_dir / 'centroides_clusters.csv'}")

    # Visualización PCA
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(scaled_data)
    df_pca = pd.DataFrame(pca_result, columns=['PC1', 'PC2'])
    df_pca['cluster'] = df['cluster']
    
    plt.figure(figsize=(10, 8))
    sns.scatterplot(x='PC1', y='PC2', hue='cluster', data=df_pca, palette='Set1', s=50, alpha=0.8)
    plt.title('Visualización de Clusters con PCA')
    plt.xlabel(f'Componente Principal 1 ({pca.explained_variance_ratio_[0]:.1%} de varianza)')
    plt.ylabel(f'Componente Principal 2 ({pca.explained_variance_ratio_[1]:.1%} de varianza)')
    plt.legend(title='Cluster')
    plt.grid(True)
    pca_path = output_dir / 'pca_clusters.png'
    plt.savefig(pca_path, dpi=150)
    plt.close()
    print(f"✅ Gráfico PCA guardado en: {pca_path}")
    
    return df

def characterize_clusters(df_with_clusters: pd.DataFrame, columns: list, output_dir: Path):
    """Genera boxplots para caracterizar los clusters."""
    print("\n--- Paso 5: Caracterizando los clusters con Boxplots ---")
    
    for var in columns:
        plt.figure(figsize=(8, 6))
        sns.boxplot(x='cluster', y=var, data=df_with_clusters)
        plt.title(f'Distribución de "{var}" por Cluster')
        plt.tight_layout()
        
        boxplot_path = output_dir / f'boxplot_{var}.png'
        plt.savefig(boxplot_path, dpi=150)
        plt.close()
    
    print(f"✅ Boxplots para todas las variables de clustering guardados en: {output_dir}")

# --- 3. FLUJO PRINCIPAL DE EJECUCIÓN ---

def main():
    """Función principal que orquesta el análisis de clustering."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    df = load_and_inspect_data(FILE_PATH)
    plot_correlation_heatmap(df, CLUSTERING_VARS, OUTPUT_DIR)
    
    df_cluster = df[CLUSTERING_VARS]
    scaler = StandardScaler()
    df_scaled = pd.DataFrame(scaler.fit_transform(df_cluster), columns=CLUSTERING_VARS)
    
    find_optimal_k(df_scaled, max_k=10, output_dir=OUTPUT_DIR)
    df_final = run_and_analyze_clustering(df, df_scaled, scaler, OPTIMAL_K, CLUSTERING_VARS, OUTPUT_DIR)
    characterize_clusters(df_final, CLUSTERING_VARS, OUTPUT_DIR)
    
    output_csv_path = OUTPUT_DIR / 'reasis_with_clusters.csv'
    df_final.to_csv(output_csv_path, index=False, sep=';', decimal='.')
    print(f"\n--- Análisis Finalizado ---")
    print(f"✅ Dataset con clusters asignados guardado en: {output_csv_path}")

if __name__ == "__main__":
    main()
