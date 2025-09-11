# GUÍA COMPLETA: K-MEANS EN R STUDIO PARA REASIS

## 🎯 PASOS PARA CLUSTERING K-MEANS

### **1. PREPARACIÓN DE DATOS**
```r
# Cargar librerías necesarias
library(readxl)          # Leer Excel
library(dplyr)           # Manipulación datos
library(cluster)         # Clustering
library(factoextra)      # Visualización clustering
library(corrplot)        # Matriz correlación
library(VIM)             # Análisis missing values
library(ggplot2)         # Gráficos

# Cargar datos desde Excel
datos <- read_excel("reasis_database_v5_final.xlsx", sheet = "indices_metodologicos")

# Verificar estructura
str(datos)
summary(datos)
```

### **2. SELECCIÓN DE VARIABLES**
```r
# Variables para clustering (solo numéricas)
variables_clustering <- datos %>%
  select(Y1_ILA, Y2_TD, Y3_PR,                    # Variables dependientes
         X1_NVC, X2_TR, X4_IDD, X5_ED, X6_CDD,    # Variables contextuales
         X10_IE, X11_RED, X12_TOE, X13_TMATRC,    # Variables organizacionales
         X14_NIVEL_EDUCATIVO, X15_MEIB,           # Variables estructurales
         X16_MODALIDAD, X17_GESTION, X18_TURNO,   # Variables operativas
         X19_ORGANIZACION_PEDAGOGICA,             # Organización
         X20_DIRECTIVOS_TOTAL, X21_MULTIPLICIDAD1, X22_MULTIPLICIDAD2,
         X24_GPMD, X25_POBLACION_DISTRITO)        # Variables demográficas

# Verificar valores perdidos
VIM::aggr(variables_clustering, col = c('navyblue', 'red'), 
          numbers = TRUE, sortVars = TRUE)
```

### **3. ESTANDARIZACIÓN**
```r
# Estandarizar variables (Z-score)
datos_std <- scale(variables_clustering)
datos_std <- as.data.frame(datos_std)

# Verificar estandarización
apply(datos_std, 2, mean)  # Debe ser ~0
apply(datos_std, 2, sd)    # Debe ser ~1
```

### **4. ANÁLISIS DE CORRELACIÓN**
```r
# Matriz de correlación
cor_matrix <- cor(datos_std)
corrplot(cor_matrix, method = "color", type = "upper", 
         order = "hclust", tl.cex = 0.8, tl.col = "black")

# Identificar variables altamente correlacionadas (>0.8)
high_cor <- which(abs(cor_matrix) > 0.8 & abs(cor_matrix) < 1, arr.ind = TRUE)
```

### **5. DETERMINACIÓN DEL NÚMERO ÓPTIMO DE CLUSTERS**

#### **A) Método del Codo (Elbow Method)**
```r
# Calcular WSS para diferentes valores de k
wss <- map_dbl(1:10, ~{
  kmeans(datos_std, centers = .x, nstart = 25, iter.max = 100)$tot.withinss
})

# Gráfico del codo
tibble(k = 1:10, wss = wss) %>%
  ggplot(aes(k, wss)) +
  geom_line() + geom_point() +
  labs(x = "Número de clusters (k)", y = "Within Sum of Squares (WSS)",
       title = "Método del Codo para K-Means") +
  theme_minimal()
```

#### **B) Método Silhouette**
```r
# Calcular silhouette para k=2 a k=10
sil_scores <- map_dbl(2:10, ~{
  km <- kmeans(datos_std, centers = .x, nstart = 25)
  mean(silhouette(km$cluster, dist(datos_std))[,3])
})

# Gráfico silhouette
tibble(k = 2:10, silhouette = sil_scores) %>%
  ggplot(aes(k, silhouette)) +
  geom_line() + geom_point() +
  labs(x = "Número de clusters (k)", y = "Silhouette Score",
       title = "Método Silhouette para K-Means") +
  theme_minimal()
```

#### **C) Método Gap Statistic**
```r
# Gap statistic (más robusto)
gap_stat <- clusGap(datos_std, FUN = kmeans, nstart = 25,
                    K.max = 10, B = 50, iter.max = 100)

# Visualizar
fviz_gap_stat(gap_stat) +
  labs(title = "Gap Statistic para K-Means")

# Número óptimo según gap
optimal_k <- maxSE(gap_stat$Tab[, "gap"], gap_stat$Tab[, "SE.sim"])
```

### **6. APLICAR K-MEANS CON K ÓPTIMO**
```r
# Aplicar k-means con k óptimo (ejemplo k=6)
set.seed(123)  # Para reproducibilidad
k_optimal <- 6  # Usar el k determinado por los métodos anteriores

kmeans_result <- kmeans(datos_std, centers = k_optimal, 
                       nstart = 25, iter.max = 100)

# Información del clustering
print(kmeans_result)
kmeans_result$size          # Tamaño de cada cluster
kmeans_result$centers       # Centroides
kmeans_result$withinss      # WSS por cluster
kmeans_result$tot.withinss  # WSS total
```

### **7. VALIDACIÓN DEL CLUSTERING**

#### **A) Silhouette Analysis**
```r
# Análisis silhouette
sil_analysis <- silhouette(kmeans_result$cluster, dist(datos_std))
fviz_silhouette(sil_analysis) +
  labs(title = "Análisis Silhouette del Clustering")

# Silhouette promedio
mean(sil_analysis[,3])
```

#### **B) Métricas de Validación**
```r
# Calinski-Harabasz Index
library(clusterSim)
ch_index <- index.G1(datos_std, kmeans_result$cluster)

# Davies-Bouldin Index  
db_index <- index.DB(datos_std, kmeans_result$cluster)

cat("Silhouette Score:", mean(sil_analysis[,3]), "\n")
cat("Calinski-Harabasz Index:", ch_index, "\n")
cat("Davies-Bouldin Index:", db_index, "\n")
```

### **8. VISUALIZACIÓN DE RESULTADOS**

#### **A) PCA para Visualización**
```r
# PCA para reducir dimensiones
pca_result <- prcomp(datos_std)
pca_data <- data.frame(pca_result$x[,1:2], 
                      cluster = as.factor(kmeans_result$cluster))

# Gráfico PCA con clusters
ggplot(pca_data, aes(PC1, PC2, color = cluster)) +
  geom_point(size = 3) +
  stat_ellipse() +
  labs(title = "Clusters K-Means visualizados con PCA",
       x = paste0("PC1 (", round(summary(pca_result)$importance[2,1]*100, 1), "%)"),
       y = paste0("PC2 (", round(summary(pca_result)$importance[2,2]*100, 1), "%)")) +
  theme_minimal()
```

#### **B) Heatmap de Centroides**
```r
# Heatmap de centroides
library(pheatmap)
centroides_df <- as.data.frame(kmeans_result$centers)
pheatmap(centroides_df, 
         scale = "none",
         cluster_rows = FALSE,
         main = "Heatmap de Centroides por Cluster")
```

### **9. CARACTERIZACIÓN DE CLUSTERS**
```r
# Agregar clusters a datos originales
datos_con_cluster <- datos %>%
  mutate(cluster = as.factor(kmeans_result$cluster))

# Estadísticas por cluster
cluster_stats <- datos_con_cluster %>%
  group_by(cluster) %>%
  summarise(
    n = n(),
    Y1_ILA_mean = mean(Y1_ILA, na.rm = TRUE),
    X1_NVC_mean = mean(X1_NVC, na.rm = TRUE),
    X2_TR_mode = names(sort(table(X2_TR), decreasing = TRUE))[1],
    .groups = 'drop'
  )

print(cluster_stats)
```

### **10. EXPORTAR RESULTADOS**
```r
# Guardar resultados
write.csv(datos_con_cluster, "resultados_clustering_kmeans.csv", row.names = FALSE)

# Guardar métricas
metricas <- data.frame(
  Metrica = c("Silhouette", "Calinski_Harabasz", "Davies_Bouldin", "WSS_Total"),
  Valor = c(mean(sil_analysis[,3]), ch_index, db_index, kmeans_result$tot.withinss)
)
write.csv(metricas, "metricas_clustering.csv", row.names = FALSE)
```

## 🎯 **VARIABLES RECOMENDADAS PARA K-MEANS**

### **Variables Principales (Alta Discriminación)**
- Y1_ILA, X1_NVC, X2_TR, X4_IDD, X5_ED
- X10_IE, X11_RED, X12_TOE

### **Variables Contextuales (Interpretación)**
- X13_TMATRC, X15_MEIB, X24_GPMD, X25_POBLACION_DISTRITO

### **Variables Opcionales (Según Correlación)**
- X14_NIVEL_EDUCATIVO, X16_MODALIDAD, X17_GESTION
- X18_TURNO, X19_ORGANIZACION_PEDAGOGICA