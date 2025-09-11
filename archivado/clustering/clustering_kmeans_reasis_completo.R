# CLUSTERING K-MEANS PROYECTO REASIS
# Script completo para R Studio

# PASO 1: CARGAR LIBRERÍAS
library(readxl)
library(dplyr)
library(cluster)
library(factoextra)
library(ggplot2)
library(corrplot)

# PASO 2: CARGAR DATOS
datos <- read_excel("reasis_database_v5_final.xlsx", 
                   sheet = "indices_metodologicos")

# Verificar estructura
print(paste("Dimensiones:", nrow(datos), "filas x", ncol(datos), "columnas"))
str(datos)

# PASO 3: SELECCIONAR VARIABLES PARA CLUSTERING
# Variables principales (recomendadas)
vars_principales <- c("Y1_ILA", "X1_NVC", "X2_TR", "X4_IDD", 
                     "X5_ED", "X6_CDD", "X11_RED", "X12_TOE")

# Variables contextuales (opcionales)
vars_contexto <- c("X10_IE", "X13_TMATRC", "X15_MEIB", 
                  "X24_GPMD", "X25_POBLACION_DISTRITO")

# Seleccionar variables finales (ajustar según análisis)
vars_clustering <- c(vars_principales, vars_contexto[1:3])

# Crear matriz de datos para clustering
datos_cluster <- datos %>%
  select(all_of(vars_clustering)) %>%
  na.omit()

print(paste("Variables seleccionadas:", length(vars_clustering)))
print(paste("Instituciones válidas:", nrow(datos_cluster)))

# PASO 4: ESTANDARIZACIÓN
datos_std <- scale(datos_cluster)
datos_std <- as.data.frame(datos_std)

# Verificar estandarización
print("Medias (deben ser ~0):")
print(round(apply(datos_std, 2, mean), 3))

# PASO 5: ANÁLISIS DE CORRELACIÓN
cor_matrix <- cor(datos_std)
corrplot(cor_matrix, method = "color", type = "upper", 
         order = "hclust", tl.cex = 0.7)

# PASO 6: DETERMINACIÓN K ÓPTIMO
# Método del codo
p1 <- fviz_nbclust(datos_std, kmeans, method = "wss", k.max = 10) +
  labs(title = "Método del Codo") +
  theme_minimal()

# Método silhouette
p2 <- fviz_nbclust(datos_std, kmeans, method = "silhouette", k.max = 10) +
  labs(title = "Método Silhouette") +
  theme_minimal()

# Mostrar gráficos
print(p1)
print(p2)

# PASO 7: APLICAR K-MEANS (ajustar k según gráficos anteriores)
set.seed(123)
k_optimo <- 6  # AJUSTAR según métodos anteriores

resultado_kmeans <- kmeans(datos_std, centers = k_optimo, 
                          nstart = 25, iter.max = 100)

# Información del clustering
print(paste("Clusters creados:", k_optimo))
print("Tamaño de clusters:")
print(table(resultado_kmeans$cluster))

# PASO 8: VALIDACIÓN
# Silhouette analysis
sil_score <- silhouette(resultado_kmeans$cluster, dist(datos_std))
sil_promedio <- mean(sil_score[,3])

print(paste("Silhouette Score promedio:", round(sil_promedio, 3)))

# Gráfico silhouette
fviz_silhouette(sil_score) +
  labs(title = paste("Análisis Silhouette (Score:", round(sil_promedio, 3), ")"))

# PASO 9: VISUALIZACIÓN
# PCA para visualización 2D
pca_result <- prcomp(datos_std)
fviz_cluster(resultado_kmeans, data = datos_std, 
             palette = "Set2", geom = "point", ellipse.type = "convex") +
  labs(title = "Clusters K-Means - Visualización PCA")

# PASO 10: CARACTERIZACIÓN DE CLUSTERS
datos_final <- datos %>%
  filter(complete.cases(datos[vars_clustering])) %>%
  mutate(cluster = as.factor(resultado_kmeans$cluster))

# Estadísticas por cluster
resumen_clusters <- datos_final %>%
  group_by(cluster) %>%
  summarise(
    n = n(),
    Y1_ILA_mean = round(mean(Y1_ILA, na.rm = TRUE), 3),
    X1_NVC_mean = round(mean(X1_NVC, na.rm = TRUE), 1),
    X2_TR_mode = as.numeric(names(sort(table(X2_TR), decreasing = TRUE))[1]),
    X11_RED_mean = round(mean(X11_RED, na.rm = TRUE), 1),
    .groups = 'drop'
  )

print("RESUMEN POR CLUSTER:")
print(resumen_clusters)

# PASO 11: EXPORTAR RESULTADOS
write.csv(datos_final, "resultados_clustering_reasis.csv", row.names = FALSE)
write.csv(resumen_clusters, "resumen_clusters_reasis.csv", row.names = FALSE)

print("CLUSTERING COMPLETADO!")
print("Archivos generados:")
print("- resultados_clustering_reasis.csv")
print("- resumen_clusters_reasis.csv")
