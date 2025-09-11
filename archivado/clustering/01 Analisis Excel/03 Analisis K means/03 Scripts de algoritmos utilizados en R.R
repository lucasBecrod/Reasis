# ===============================================================================
# ANÁLISIS K-MEANS PARA TIPOLOGÍAS INSTITUCIONALES
# Proyecto REASIS - Fe y Alegría
# ===============================================================================

# 1. CARGAR LIBRERÍAS NECESARIAS
# ===============================================================================
library(readxl)      # Para leer archivos Excel
library(dplyr)       # Para manipulación de datos
library(cluster)     # Para análisis de clustering
library(factoextra)  # Para visualizaciones de clustering
library(ggplot2)     # Para gráficos avanzados
library(gridExtra)   # Para combinar gráficos

# 2. CARGAR Y PREPARAR DATOS
# ===============================================================================
# Ruta del archivo
ruta_archivo <- "C:/Users/lucas/Proyectos/Reasis/01 Analisis Excel/reasis_database_v5_final.xlsx"

# Cargar datos
datos_raw <- read_excel(ruta_archivo, 
                        sheet = "indices_metodologicos",
                        range = "A1:AC164")

print(paste("Datos cargados:", nrow(datos_raw), "filas,", ncol(datos_raw), "columnas"))

# 3. SELECCIÓN DE VARIABLES PARA CLUSTERING
# ===============================================================================

# Variables seleccionadas basadas en análisis de correlación previo
variables_clustering_final <- c(
  "Y1_ILA",              # Logro académico
  "Y2_TD",               # Tendencia desempeño  
  "X1_NVC",              # Vulnerabilidad contextual
  "X2_TR",               # Ruralidad
  "X4_IDD",              # Desempeño docente
  "X11_RED",             # Ratio estudiante-docente
  "X12_TOE",             # Organización escolar
  "X13_TMATRC",          # Tendencia matrícula
  "X14_NIVEL_EDUCATIVO", # Nivel educativo
  "ALTITUD_MSNM"         # Altitud (factor geográfico)
)

# Crear dataset final para clustering
datos_clustering_final <- datos_raw %>%
  select(CODIGO_MODULAR, NOMBRE_INSTITUCION, all_of(variables_clustering_final))

print("=== VARIABLES SELECCIONADAS PARA CLUSTERING ===")
print(paste("Instituciones:", nrow(datos_clustering_final)))
print("Variables:")
print(variables_clustering_final)

# Verificar matriz de correlación final (sin multicolinealidad)
matriz_final <- cor(datos_clustering_final[variables_clustering_final], use = "complete.obs")
correlacion_maxima <- max(abs(matriz_final[upper.tri(matriz_final)]))
print(paste("Correlación máxima entre variables:", round(correlacion_maxima, 3)))

# 4. ESTANDARIZACIÓN DE VARIABLES
# ===============================================================================

print("=== ESTANDARIZACIÓN Z-SCORE ===")

# Separar variables numéricas para estandarización
variables_numericas <- datos_clustering_final %>%
  select(all_of(variables_clustering_final)) %>%
  select_if(is.numeric)

# Aplicar estandarización Z-score
datos_estandarizados <- scale(variables_numericas)
datos_estandarizados <- as.data.frame(datos_estandarizados)

# Verificar estandarización
print("Medias después de estandarización (deben ser ~0):")
print(round(colMeans(datos_estandarizados), 3))

print("Desviaciones estándar después de estandarización (deben ser ~1):")
print(round(apply(datos_estandarizados, 2, sd), 3))

# Combinar con identificadores
datos_clustering_z <- data.frame(
  CODIGO_MODULAR = datos_clustering_final$CODIGO_MODULAR,
  NOMBRE_INSTITUCION = datos_clustering_final$NOMBRE_INSTITUCION,
  datos_estandarizados
)

print("=== DATOS ESTANDARIZADOS PREPARADOS ===")

# ===============================================================================
# 5. DETERMINACIÓN DEL NÚMERO ÓPTIMO DE CLÚSTERES
# ===============================================================================

print("=== DETERMINACIÓN K ÓPTIMO ===")

set.seed(123)  # Para reproducibilidad

# MÉTODO 1: Análisis del Codo (Elbow Method)
print("=== MÉTODO DEL CODO ===")
elbow_plot <- fviz_nbclust(datos_estandarizados, kmeans, method = "wss", k.max = 10)
print(elbow_plot)

# MÉTODO 2: Análisis Silhouette
print("=== MÉTODO SILHOUETTE ===")
silhouette_plot <- fviz_nbclust(datos_estandarizados, kmeans, method = "silhouette", k.max = 10)
print(silhouette_plot)

# MÉTODO 3: Cálculo manual WCSS para análisis detallado
print("=== CÁLCULO MANUAL WCSS ===")

k_values <- 2:8
wcss_manual <- c()

for(i in k_values) {
  kmeans_result <- kmeans(datos_estandarizados, centers = i, nstart = 25)
  wcss_manual[i-1] <- kmeans_result$tot.withinss
}

# Mostrar resultados numéricos
wcss_df <- data.frame(K = k_values, WCSS = round(wcss_manual, 2))
print("WCSS por K:")
print(wcss_df)

# Calcular mejora relativa
mejora <- c(NA)
for(i in 2:length(wcss_manual)) {
  mejora[i] <- round((wcss_manual[i-1] - wcss_manual[i]) / wcss_manual[i-1] * 100, 2)
}

mejora_df <- data.frame(K = k_values, WCSS = round(wcss_manual, 2), Mejora_Porcentual = mejora)
print("Mejora porcentual por K:")
print(mejora_df)

# ===============================================================================
# 6. APLICACIÓN DE K-MEANS CON DIFERENTES VALORES DE K
# ===============================================================================

print("=== APLICACIÓN DE K-MEANS ===")

set.seed(123)

# Probar diferentes valores de K
k_valores_test <- c(2, 3, 4, 5)
resultados_kmeans <- list()

for(k in k_valores_test) {
  resultado <- kmeans(datos_estandarizados, centers = k, nstart = 25)
  resultados_kmeans[[paste0("k", k)]] <- resultado
  
  print(paste("=== K =", k, "==="))
  print(paste("Tamaño clusters:", paste(resultado$size, collapse = ", ")))
  print(paste("WCSS:", round(resultado$tot.withinss, 2)))
  print(paste("Silhouette promedio:", round(mean(silhouette(resultado$cluster, dist(datos_estandarizados))[, 3]), 3)))
}

# ===============================================================================
# 7. CARACTERIZACIÓN DETALLADA DE CLÚSTERES (EJEMPLO K=4)
# ===============================================================================

print("=== CARACTERIZACIÓN DETALLADA K=4 ===")

# Seleccionar solución K=4 como ejemplo
kmeans_final <- resultados_kmeans$k4
k_final <- 4

# Agregar cluster al dataset
datos_finales <- datos_clustering_z
datos_finales$Cluster <- kmeans_final$cluster

# Caracterización estadística por cluster
caracterizacion <- data.frame()

for(i in 1:k_final) {
  cluster_data <- datos_finales[datos_finales$Cluster == i, ]
  cluster_stats <- cluster_data %>%
    select(all_of(variables_clustering_final)) %>%
    summarise_all(list(
      n = ~n(),
      media = ~round(mean(., na.rm = TRUE), 3),
      mediana = ~round(median(., na.rm = TRUE), 3),
      sd = ~round(sd(., na.rm = TRUE), 3)
    )) %>%
    mutate(Cluster = i) %>%
    select(Cluster, everything())
  
  caracterizacion <- rbind(caracterizacion, cluster_stats)
}

print("Caracterización estadística por cluster:")
print(caracterizacion)

# Estadísticas descriptivas simples por cluster
print("=== ESTADÍSTICAS DESCRIPTIVAS POR CLUSTER ===")

for(i in 1:k_final) {
  cat("\n=== CLUSTER", i, "===\n")
  cluster_i <- datos_finales[datos_finales$Cluster == i, ]
  cat("Tamaño:", nrow(cluster_i), "instituciones\n")
  
  # Medias por cluster
  medias_cluster <- round(colMeans(cluster_i[, variables_clustering_final]), 3)
  cat("Características principales:\n")
  for(var in names(medias_cluster)) {
    cat(paste("•", var, ":", medias_cluster[var], "\n"))
  }
}





# ===============================================================================
# GRÁFICOS INDIVIDUALES PARA CADA K - VERSIÓN CON COLORES TEMÁTICOS
# ===============================================================================

# Definir colores temáticos oficiales para K=4
colores_tematicos_k4 <- c(
  "#2980B9",  # Azul - Tradicionales Estables (Clúster 1)
  "#F1C40F",  # Dorado - Élite Institucional (Clúster 2)
  "#27AE60",  # Verde - Rurales Resilientes (Clúster 3)
  "#E67E22"   # Naranja - Emergentes Complejas (Clúster 4)
)

# Función para crear gráfico individual con colores apropiados
crear_grafico_k <- function(resultado_kmeans, k_valor, datos_estand) {
  
  # Selección de paleta de colores según K
  paleta_colores <- if(k_valor == 2) {
    c("#E74C3C", "#3498DB")
  } else if(k_valor == 3) {
    c("#E74C3C", "#F39C12", "#3498DB")
  } else if(k_valor == 4) {
    # USAR COLORES TEMÁTICOS OFICIALES PARA K=4
    colores_tematicos_k4
  } else if(k_valor == 5) {
    c("#E74C3C", "#F39C12", "#3498DB", "#9B59B6", "#1ABC9C")
  } else {
    rainbow(k_valor)
  }
  
  # Crear gráfico con la paleta seleccionada
  fviz_cluster(resultado_kmeans, data = datos_estand,
               palette = paleta_colores,
               geom = "point",
               ellipse.type = "convex",
               ggtheme = theme_bw(),
               main = paste("K =", k_valor, "| WCSS =", round(resultado_kmeans$tot.withinss, 0)),
               subtitle = paste("Distribución:", paste(resultado_kmeans$size, collapse = "-")))
}

# Generar gráficos individuales con colores ajustados
print("=== GENERANDO GRÁFICOS INDIVIDUALES CON COLORES TEMÁTICOS ===")

# K = 2
plot_k2 <- crear_grafico_k(resultados_kmeans$k2, 2, datos_estandarizados)
print("Gráfico K=2:")
print(plot_k2)

# K = 3  
plot_k3 <- crear_grafico_k(resultados_kmeans$k3, 3, datos_estandarizados)
print("Gráfico K=3:")
print(plot_k3)

# K = 4 - CON COLORES TEMÁTICOS OFICIALES
plot_k4 <- crear_grafico_k(resultados_kmeans$k4, 4, datos_estandarizados)
print("Gráfico K=4 con colores temáticos:")
print(plot_k4)

# Verificar colores aplicados para K=4
print("Colores temáticos aplicados a K=4:")
print("• Clúster 1 (Tradicionales Estables): #2980B9 (Azul)")
print("• Clúster 2 (Élite Institucional): #F1C40F (Dorado)")
print("• Clúster 3 (Rurales Resilientes): #27AE60 (Verde)")
print("• Clúster 4 (Emergentes Complejas): #E67E22 (Naranja)")

# K = 5
plot_k5 <- crear_grafico_k(resultados_kmeans$k5, 5, datos_estandarizados)
print("Gráfico K=5:")
print(plot_k5)

# K = 9
plot_k9 <- crear_grafico_k(resultados_kmeans$k9, 9, datos_estandarizados)
print("Gráfico K=9:")
print(plot_k9)

# ===============================================================================
# PANEL COMPARATIVO DE TODOS LOS K
# ===============================================================================

print("=== PANEL COMPARATIVO ===")

# Crear panel con grid.arrange
panel_comparativo <- grid.arrange(plot_k2, plot_k3, plot_k4, plot_k5, 
                                  ncol = 2, nrow = 2,
                                  top = "Comparación de Soluciones K-Means\nProyecto REASIS - Fe y Alegría")

# Mostrar K=9 por separado (por espacio)
print("Gráfico K=9 (separado por tamaño):")
print(plot_k9)

# ===============================================================================
# TABLA RESUMEN COMPARATIVA
# ===============================================================================

print("=== TABLA RESUMEN COMPARATIVA ===")

# Calcular métricas para todos los K
k_valores_todos <- c(2, 3, 4, 5, 9)
resumen_comparativo <- data.frame()

for(k in k_valores_todos) {
  resultado <- resultados_kmeans[[paste0("k", k)]]
  
  # Calcular silhouette
  sil_score <- silhouette(resultado$cluster, dist(datos_estandarizados))
  sil_promedio <- round(mean(sil_score[, 3]), 3)
  
  # Agregar a resumen
  resumen_comparativo <- rbind(resumen_comparativo, data.frame(
    K = k,
    WCSS = round(resultado$tot.withinss, 2),
    Silhouette = sil_promedio,
    Clusters_Size = paste(resultado$size, collapse = "-"),
    Menor_Cluster = min(resultado$size),
    Mayor_Cluster = max(resultado$size),
    Balanceado = ifelse(max(resultado$size)/min(resultado$size) < 3, "Sí", "No")
  ))
}

print("Resumen comparativo de todas las soluciones:")
print(resumen_comparativo)

# ===============================================================================
# GRÁFICO DE MÉTRICAS DE CALIDAD
# ===============================================================================

print("=== GRÁFICO DE MÉTRICAS DE CALIDAD ===")

# Crear gráfico de WCSS vs Silhouette
library(ggplot2)

# Preparar datos para gráfico
metricas_df <- data.frame(
  K = resumen_comparativo$K,
  WCSS = resumen_comparativo$WCSS,
  Silhouette = resumen_comparativo$Silhouette
)

# Gráfico 1: WCSS por K (Método del Codo Manual)
plot_wcss <- ggplot(metricas_df, aes(x = K, y = WCSS)) +
  geom_line(color = "#E74C3C", size = 1.2) +
  geom_point(color = "#E74C3C", size = 3) +
  geom_text(aes(label = WCSS), vjust = -0.5, size = 3) +
  scale_x_continuous(breaks = c(2, 3, 4, 5, 9)) +
  labs(title = "Within-Cluster Sum of Squares (WCSS)",
       subtitle = "Método del Codo - Menor es mejor",
       x = "Número de Clusters (K)", 
       y = "WCSS") +
  theme_minimal() +
  theme(plot.title = element_text(hjust = 0.5, face = "bold"),
        plot.subtitle = element_text(hjust = 0.5))

print(plot_wcss)

# Gráfico 2: Silhouette por K
plot_silhouette <- ggplot(metricas_df, aes(x = K, y = Silhouette)) +
  geom_line(color = "#3498DB", size = 1.2) +
  geom_point(color = "#3498DB", size = 3) +
  geom_text(aes(label = Silhouette), vjust = -0.5, size = 3) +
  scale_x_continuous(breaks = c(2, 3, 4, 5, 9)) +
  labs(title = "Coeficiente de Silhouette Promedio",
       subtitle = "Calidad de Clustering - Mayor es mejor",
       x = "Número de Clusters (K)", 
       y = "Silhouette Score") +
  theme_minimal() +
  theme(plot.title = element_text(hjust = 0.5, face = "bold"),
        plot.subtitle = element_text(hjust = 0.5))

print(plot_silhouette)

# Combinar ambos gráficos
metricas_panel <- grid.arrange(plot_wcss, plot_silhouette, ncol = 2,
                               top = "Métricas de Calidad por Número de Clusters")

# ===============================================================================
# ANÁLISIS DE DISTRIBUCIÓN DE TAMAÑOS
# ===============================================================================

print("=== ANÁLISIS DE DISTRIBUCIÓN DE TAMAÑOS ===")

# Crear gráfico de distribución de tamaños
distribuciones <- data.frame()

for(k in k_valores_todos) {
  resultado <- resultados_kmeans[[paste0("k", k)]]
  for(i in 1:length(resultado$size)) {
    distribuciones <- rbind(distribuciones, data.frame(
      K = paste("K =", k),
      Cluster = paste("C", i, sep=""),
      Tamaño = resultado$size[i],
      Porcentaje = round(resultado$size[i] / sum(resultado$size) * 100, 1)
    ))
  }
}

# Gráfico de barras por K
plot_distribucion <- ggplot(distribuciones, aes(x = Cluster, y = Tamaño, fill = K)) +
  geom_col() +
  geom_text(aes(label = paste0(Tamaño, "\n(", Porcentaje, "%)")), 
            position = position_dodge(width = 0.9), vjust = 0.5, size = 2.5) +
  facet_wrap(~K, scales = "free_x") +
  labs(title = "Distribución del Tamaño de Clusters",
       subtitle = "Número y porcentaje de instituciones por cluster",
       x = "Cluster", y = "Número de Instituciones") +
  theme_minimal() +
  theme(plot.title = element_text(hjust = 0.5, face = "bold"),
        plot.subtitle = element_text(hjust = 0.5),
        legend.position = "none",
        axis.text.x = element_text(angle = 45, hjust = 1))

print(plot_distribucion)

# ===============================================================================
# RECOMENDACIÓN BASADA EN MÉTRICAS
# ===============================================================================

print("=== RECOMENDACIÓN BASADA EN MÉTRICAS ===")

# Encontrar K óptimo según diferentes criterios
k_mejor_silhouette <- resumen_comparativo$K[which.max(resumen_comparativo$Silhouette)]
k_mas_balanceado <- resumen_comparativo$K[resumen_comparativo$Balanceado == "Sí"][1]

# Análisis del método del codo
wcss_vector <- resumen_comparativo$WCSS
mejoras_wcss <- c(NA)
for(i in 2:length(wcss_vector)) {
  mejoras_wcss[i] <- round((wcss_vector[i-1] - wcss_vector[i]) / wcss_vector[i-1] * 100, 2)
}

# Encontrar el "codo" (donde la mejora se reduce significativamente)
punto_codo <- which(mejoras_wcss < 10 & !is.na(mejoras_wcss))[1]
if(!is.na(punto_codo)) {
  k_codo <- k_valores_todos[punto_codo]
} else {
  k_codo <- k_valores_todos[length(wcss_vector)-1]  # Penúltimo si no hay codo claro
}

cat("\n=== ANÁLISIS DE RECOMENDACIÓN ===\n")
cat("📊 CRITERIOS DE EVALUACIÓN:\n")
cat(paste("• Mejor Silhouette Score: K =", k_mejor_silhouette, 
          "(", resumen_comparativo$Silhouette[resumen_comparativo$K == k_mejor_silhouette], ")\n"))
cat(paste("• Punto del Codo (WCSS): K =", k_codo, "\n"))
cat(paste("• Más Balanceado: K =", k_mas_balanceado, "\n"))

# Análisis de clusters pequeños
clusters_pequeños <- resumen_comparativo[resumen_comparativo$Menor_Cluster <= 10, ]
if(nrow(clusters_pequeños) > 0) {
  cat("\n⚠️ CLUSTERS PEQUEÑOS DETECTADOS:\n")
  for(i in 1:nrow(clusters_pequeños)) {
    cat(paste("• K =", clusters_pequeños$K[i], 
              "tiene cluster mínimo de", clusters_pequeños$Menor_Cluster[i], "instituciones\n"))
  }
}

cat("\n🎯 RECOMENDACIÓN PRELIMINAR:\n")
cat("Basado en las métricas, se sugiere evaluar principalmente:\n")
cat(paste("• K =", k_mejor_silhouette, "(mejor calidad de clustering)\n"))
if(k_codo != k_mejor_silhouette) {
  cat(paste("• K =", k_codo, "(método del codo)\n"))
}

print("\n=== GRÁFICOS GENERADOS EXITOSAMENTE ===")
print("Revisa los gráficos para tomar la decisión final sobre K óptimo")









# ===============================================================================
# GRÁFICOS CON NOMENCLATURA FINAL APROBADA
# Tipologías Institucionales Fe y Alegría - 2025
# ===============================================================================

library(ggplot2)
library(gridExtra)
library(dplyr)
library(cluster)
library(factoextra)

# ===============================================================================
# NOMENCLATURA FINAL APROBADA Y COLORES TEMÁTICOS
# ===============================================================================

print("=== APLICANDO NOMENCLATURA FINAL APROBADA ===")

# Nombres finales confirmados
nombres_finales_aprobados <- c(
  "Tradicionales Estables",    # Cluster 1: n=77, 47.2%
  "Élite Institucional",       # Cluster 2: n=7, 4.3%
  "Rurales Resilientes",       # Cluster 3: n=50, 30.7%
  "Emergentes Complejas"       # Cluster 4: n=29, 17.8%
)

# Paleta de colores temática según significado de cada tipología
colores_tematicos <- c(
  "#2980B9",  # Azul - Tradicionales Estables (estabilidad, confianza)
  "#F1C40F",  # Dorado - Élite Institucional (excelencia, prestigio)
  "#27AE60",  # Verde - Rurales Resilientes (crecimiento, resiliencia)
  "#E67E22"   # Naranja - Emergentes Complejas (dinamismo, innovación)
)

print("Colores temáticos asignados:")
print("• Azul: Tradicionales Estables (estabilidad)")
print("• Dorado: Élite Institucional (excelencia)")  
print("• Verde: Rurales Resilientes (resiliencia)")
print("• Naranja: Emergentes Complejas (dinamismo)")

# Datos de distribución con nomenclatura final
distribucion_final_aprobada <- data.frame(
  Cluster = c("Clúster 1", "Clúster 2", "Clúster 3", "Clúster 4"),
  Instituciones = c(77, 7, 50, 29),
  Porcentaje = c(47.2, 4.3, 30.7, 17.8),
  Tipologia_Final = nombres_finales_aprobados
)

# Actualizar datos finales con nomenclatura aprobada
datos_finales$Tipologia_Aprobada <- case_when(
  datos_finales$Cluster == 1 ~ "Tradicionales Estables",
  datos_finales$Cluster == 2 ~ "Élite Institucional", 
  datos_finales$Cluster == 3 ~ "Rurales Resilientes",
  datos_finales$Cluster == 4 ~ "Emergentes Complejas"
)

print("Nomenclatura final aplicada exitosamente")
print(distribucion_final_aprobada)

# ===============================================================================
# GRÁFICO 1: DISTRIBUCIÓN DE INSTITUCIONES CON NOMENCLATURA FINAL
# ===============================================================================

print("=== GENERANDO GRÁFICO 1: DISTRIBUCIÓN FINAL ===")

grafico_distribucion_final <- ggplot(distribucion_final_aprobada, 
                                     aes(x = reorder(Cluster, -Instituciones), 
                                         y = Instituciones, 
                                         fill = Cluster)) +
  geom_col(alpha = 0.8, width = 0.7, color = "white", size = 0.5) +
  
  # Números y porcentajes en la parte superior
  geom_text(aes(label = paste0(Instituciones, "\n(", Porcentaje, "%)")), 
            vjust = -0.3, size = 4, fontface = "bold", color = "black") +
  
  # Nombres de tipología finales con color de texto apropiado
  geom_text(aes(label = Tipologia_Final, y = Instituciones/2), 
            size = 3.3, fontface = "bold", 
            color = c("white", "black", "white", "white"),  # Texto según contraste de cada color
            hjust = 0.5) +
  
  # Colores temáticos por significado de tipología
  scale_fill_manual(values = c("Clúster 1" = "#2980B9",    # Azul - Estabilidad/Tradición
                               "Clúster 2" = "#F1C40F",    # Dorado - Excelencia/Élite
                               "Clúster 3" = "#27AE60",    # Verde - Resiliencia/Crecimiento
                               "Clúster 4" = "#E67E22")) + # Naranja - Emergencia/Dinamismo
  
  labs(title = "Tipologías Institucionales Fe y Alegría",
       subtitle = "Análisis K-Means K=4 | Total: 163 instituciones educativas",
       x = "Tipologías Identificadas",
       y = "Número de Instituciones",
       caption = "Fuente: Análisis clustering K-Means | 2025") +
  
  theme_minimal() +
  theme(
    plot.title = element_text(size = 15, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(size = 12, hjust = 0.5, color = "gray40"),
    axis.title = element_text(size = 11, face = "bold"),
    axis.text = element_text(size = 10),
    legend.position = "none",
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank(),
    plot.caption = element_text(size = 9, color = "gray50"),
    axis.text.x = element_text(size = 10, face = "bold")
  ) +
  
  ylim(0, max(distribucion_final_aprobada$Instituciones) * 1.2)

print(grafico_distribucion_final)


# ===============================================================================
# GRÁFICO 1: DISTRIBUCIÓN DE INSTITUCIONES CON ETIQUETAS CENTRADAS
# ===============================================================================

print("=== GENERANDO GRÁFICO 1: DISTRIBUCIÓN FINAL CON ETIQUETAS CENTRADAS ===")

# Crear versión corta de nombres con saltos de línea para las barras
nombres_centrados <- c(
  "Tradicionales\nEstables",    # Clúster 1
  "Élite\nInstitucional",       # Clúster 2  
  "Rurales\nResilientess",      # Clúster 3
  "Emergentes\nComplejas"       # Clúster 4
)

# Actualizar el dataframe con nombres centrados
distribucion_final_aprobada$Tipologia_Centrada <- nombres_centrados

grafico_distribucion_final <- ggplot(distribucion_final_aprobada, 
                                     aes(x = reorder(Cluster, -Instituciones), 
                                         y = Instituciones, 
                                         fill = Cluster)) +
  geom_col(alpha = 0.8, width = 0.7, color = "white", size = 0.5) +
  
  # Números y porcentajes en la parte superior
  geom_text(aes(label = paste0(Instituciones, "\n(", Porcentaje, "%)")), 
            vjust = -0.3, size = 4, fontface = "bold", color = "black") +
  
  # Nombres de tipología centrados con salto de línea
  geom_text(aes(label = Tipologia_Centrada, y = Instituciones/2), 
            size = 3.2, fontface = "bold", 
            color = c("white", "black", "white", "white"),  # Texto según contraste de cada color
            hjust = 0.5, vjust = 0.5,  # Centrado horizontal y vertical
            lineheight = 0.8) +  # Espaciado entre líneas
  
  # Colores temáticos por significado de tipología
  scale_fill_manual(values = c("Clúster 1" = "#2980B9",    # Azul - Estabilidad/Tradición
                               "Clúster 2" = "#F1C40F",    # Dorado - Excelencia/Élite
                               "Clúster 3" = "#27AE60",    # Verde - Resiliencia/Crecimiento
                               "Clúster 4" = "#E67E22")) + # Naranja - Emergencia/Dinamismo
  
  labs(title = "Tipologías Institucionales Fe y Alegría",
       subtitle = "Análisis K-Means K=4 | Total: 163 instituciones educativas",
       x = "Tipologías Identificadas",
       y = "Número de Instituciones",
       caption = "Fuente: Análisis clustering K-Means | 2025") +
  
  theme_minimal() +
  theme(
    plot.title = element_text(size = 15, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(size = 12, hjust = 0.5, color = "gray40"),
    axis.title = element_text(size = 11, face = "bold"),
    axis.text = element_text(size = 10),
    legend.position = "none",
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank(),
    plot.caption = element_text(size = 9, color = "gray50"),
    axis.text.x = element_text(size = 10, face = "bold")
  ) +
  
  ylim(0, max(distribucion_final_aprobada$Instituciones) * 1.2)

print(grafico_distribucion_final)

# ===============================================================================
# ALTERNATIVA CON AJUSTE AUTOMÁTICO DE TEXTO
# ===============================================================================

# Función alternativa para ajustar automáticamente el texto
library(stringr)

ajustar_etiquetas_automatico <- function(texto, ancho_max = 12) {
  # Función para crear saltos de línea automáticos
  str_wrap(texto, width = ancho_max)
}

# Aplicar ajuste automático
distribucion_final_aprobada$Tipologia_Auto <- sapply(distribucion_final_aprobada$Tipologia_Final, 
                                                     ajustar_etiquetas_automatico)

# Versión con ajuste automático
grafico_distribucion_automatico <- ggplot(distribucion_final_aprobada, 
                                          aes(x = reorder(Cluster, -Instituciones), 
                                              y = Instituciones, 
                                              fill = Cluster)) +
  geom_col(alpha = 0.8, width = 0.7, color = "white", size = 0.5) +
  
  # Números y porcentajes en la parte superior
  geom_text(aes(label = paste0(Instituciones, "\n(", Porcentaje, "%)")), 
            vjust = -0.3, size = 4, fontface = "bold", color = "black") +
  
  # Nombres de tipología con ajuste automático
  geom_text(aes(label = Tipologia_Auto, y = Instituciones/2), 
            size = 3.0, fontface = "bold", 
            color = c("white", "black", "white", "white"),
            hjust = 0.5, vjust = 0.5,
            lineheight = 0.85) +
  
  # Colores temáticos
  scale_fill_manual(values = c("Clúster 1" = "#2980B9",
                               "Clúster 2" = "#F1C40F",
                               "Clúster 3" = "#27AE60",
                               "Clúster 4" = "#E67E22")) +
  
  labs(title = "Tipologías Institucionales Fe y Alegría",
       subtitle = "Análisis K-Means K=4 | Total: 163 instituciones educativas",
       x = "Tipologías Identificadas",
       y = "Número de Instituciones",
       caption = "Fuente: Análisis clustering K-Means | 2025") +
  
  theme_minimal() +
  theme(
    plot.title = element_text(size = 15, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(size = 12, hjust = 0.5, color = "gray40"),
    axis.title = element_text(size = 11, face = "bold"),
    axis.text = element_text(size = 10),
    legend.position = "none",
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank(),
    plot.caption = element_text(size = 9, color = "gray50"),
    axis.text.x = element_text(size = 10, face = "bold")
  ) +
  
  ylim(0, max(distribucion_final_aprobada$Instituciones) * 1.2)

print("Gráfico con ajuste automático:")
print(grafico_distribucion_automatico)

# ===============================================================================
# OPCIÓN CON CONTROL FINO DE POSICIONAMIENTO
# ===============================================================================

# Para máximo control, definir posiciones específicas
grafico_distribucion_control_fino <- ggplot(distribucion_final_aprobada, 
                                            aes(x = reorder(Cluster, -Instituciones), 
                                                y = Instituciones, 
                                                fill = Cluster)) +
  geom_col(alpha = 0.8, width = 0.7, color = "white", size = 0.5) +
  
  # Números y porcentajes en la parte superior
  geom_text(aes(label = paste0(Instituciones, "\n(", Porcentaje, "%)")), 
            vjust = -0.3, size = 4, fontface = "bold", color = "black") +
  
  # Etiquetas individuales con control fino
  geom_text(data = subset(distribucion_final_aprobada, Cluster == "Clúster 1"),
            aes(label = "Tradicionales\nEstables", y = Instituciones/2), 
            size = 3.2, fontface = "bold", color = "white", hjust = 0.5, vjust = 0.5, lineheight = 0.8) +
  
  geom_text(data = subset(distribucion_final_aprobada, Cluster == "Clúster 2"),
            aes(label = "Élite\nInstitucional", y = Instituciones/2), 
            size = 3.2, fontface = "bold", color = "black", hjust = 0.5, vjust = 0.5, lineheight = 0.8) +
  
  geom_text(data = subset(distribucion_final_aprobada, Cluster == "Clúster 3"),
            aes(label = "Rurales\nResilientess", y = Instituciones/2), 
            size = 3.2, fontface = "bold", color = "white", hjust = 0.5, vjust = 0.5, lineheight = 0.8) +
  
  geom_text(data = subset(distribucion_final_aprobada, Cluster == "Clúster 4"),
            aes(label = "Emergentes\nComplejas", y = Instituciones/2), 
            size = 3.2, fontface = "bold", color = "white", hjust = 0.5, vjust = 0.5, lineheight = 0.8) +
  
  # Colores temáticos
  scale_fill_manual(values = c("Clúster 1" = "#2980B9",
                               "Clúster 2" = "#F1C40F",
                               "Clúster 3" = "#27AE60",
                               "Clúster 4" = "#E67E22")) +
  
  labs(title = "Tipologías Institucionales Fe y Alegría",
       subtitle = "Análisis K-Means K=4 | Total: 163 instituciones educativas",
       x = "Tipologías Identificadas",
       y = "Número de Instituciones",
       caption = "Fuente: Análisis clustering K-Means | 2025") +
  
  theme_minimal() +
  theme(
    plot.title = element_text(size = 15, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(size = 12, hjust = 0.5, color = "gray40"),
    axis.title = element_text(size = 11, face = "bold"),
    axis.text = element_text(size = 10),
    legend.position = "none",
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank(),
    plot.caption = element_text(size = 9, color = "gray50"),
    axis.text.x = element_text(size = 10, face = "bold")
  ) +
  
  ylim(0, max(distribucion_final_aprobada$Instituciones) * 1.2)

print("Gráfico con control fino:")
print(grafico_distribucion_control_fino)

# ===============================================================================
# GRÁFICO 2: CONFIGURACIÓN ESPACIAL CON NOMENCLATURA FINAL
# ===============================================================================

print("=== GENERANDO GRÁFICO 2: CONFIGURACIÓN ESPACIAL ===")

# Crear visualización de clusters con colores temáticos
grafico_espacial_final <- fviz_cluster(kmeans_final, data = datos_estandarizados,
                                       palette = c("#2980B9", "#F1C40F", "#27AE60", "#E67E22"),
                                       geom = "point",
                                       ellipse.type = "convex",
                                       ggtheme = theme_bw(),
                                       main = "Configuración Espacial de Tipologías Institucionales",
                                       subtitle = "Solución K=4 con Nomenclatura Definitiva")

# Personalizar el gráfico espacial
grafico_espacial_final <- grafico_espacial_final +
  theme(
    plot.title = element_text(size = 14, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(size = 12, hjust = 0.5, color = "gray40"),
    axis.title = element_text(size = 11, face = "bold"),
    legend.title = element_text(size = 10, face = "bold"),
    legend.text = element_text(size = 9)
  ) +
  labs(caption = "Análisis de Componentes Principales (PCA) | 2025")

print(grafico_espacial_final)

# ===============================================================================
# GRÁFICO 3: VALIDACIÓN SILHOUETTE CON NOMENCLATURA FINAL
# ===============================================================================

print("=== GENERANDO GRÁFICO 3: VALIDACIÓN SILHOUETTE ===")

# Actualizar nombres en silhouette_df
silhouette_df_final <- silhouette_df
silhouette_df_final$Tipologia <- case_when(
  silhouette_df_final$Cluster == "Clúster 1" ~ "Tradicionales\nEstables",
  silhouette_df_final$Cluster == "Clúster 2" ~ "Élite\nInstitucional",
  silhouette_df_final$Cluster == "Clúster 3" ~ "Rurales\nResilientess",
  silhouette_df_final$Cluster == "Clúster 4" ~ "Emergentes\nComplejas"
)

# Gráfico Silhouette con nomenclatura final
grafico_silhouette_final <- ggplot(silhouette_df_final, 
                                   aes(x = reorder(Tipologia, Silhouette_Value, median), 
                                       y = Silhouette_Value, 
                                       fill = Cluster)) +
  geom_boxplot(alpha = 0.7, outlier.alpha = 0.6) +
  geom_hline(yintercept = 0, linetype = "dashed", color = "red", size = 0.8) +
  geom_hline(yintercept = mean(silhouette_df_final$Silhouette_Value), 
             linetype = "solid", color = "blue", size = 0.8) +
  
  scale_fill_manual(values = c("Clúster 1" = "#2980B9",    # Azul - Estabilidad/Tradición
                               "Clúster 2" = "#F1C40F",    # Dorado - Excelencia/Élite
                               "Clúster 3" = "#27AE60",    # Verde - Resiliencia/Crecimiento
                               "Clúster 4" = "#E67E22")) + # Naranja - Emergencia/Dinamismo
  
  labs(title = "Validación de Calidad por Tipología",
       subtitle = paste("Coeficiente de Silhouette Promedio:", 
                        round(mean(silhouette_df_final$Silhouette_Value), 3)),
       x = "Tipologías Institucionales",
       y = "Coeficiente de Silhouette",
       caption = "Valores positivos indican asignación correcta al cluster") +
  
  theme_minimal() +
  theme(
    plot.title = element_text(size = 14, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(size = 12, hjust = 0.5, color = "gray40"),
    axis.title = element_text(size = 11, face = "bold"),
    axis.text = element_text(size = 10),
    legend.position = "none",
    panel.grid.minor = element_blank(),
    plot.caption = element_text(size = 9, color = "gray50"),
    axis.text.x = element_text(size = 9, face = "bold")
  ) +
  
  ylim(-0.3, 1.0)

print(grafico_silhouette_final)

# ===============================================================================
# PANEL COMBINADO PARA PRESENTACIÓN EJECUTIVA
# ===============================================================================

print("=== GENERANDO PANEL EJECUTIVO ===")

# Crear panel combinado de tres gráficos
panel_ejecutivo <- grid.arrange(
  grafico_distribucion_final,
  arrangeGrob(grafico_espacial_final, grafico_silhouette_final, ncol = 2),
  ncol = 1, nrow = 2,
  heights = c(1, 1)
)

print("Panel ejecutivo generado exitosamente")

# ===============================================================================
# TABLA RESUMEN EJECUTIVA CON NOMENCLATURA FINAL
# ===============================================================================

print("=== TABLA RESUMEN EJECUTIVA ===")

# Crear tabla de características principales
tabla_ejecutiva_final <- data.frame(
  Tipologia = nombres_finales_aprobados,
  Cluster = paste("Clúster", 1:4),
  n = distribucion_final_aprobada$Instituciones,
  Porcentaje = paste0(distribucion_final_aprobada$Porcentaje, "%"),
  Caracteristica_Principal = c(
    "Estructura consolidada con trayectoria estable",
    "Excelencia académica en contextos urbanos",
    "Mejoramiento constante en contextos rurales", 
    "Organización compleja con crecimiento matricular"
  ),
  Contexto_Geografico = c(
    "Baja altitud, distritos poblados",
    "Centros urbanos desarrollados",
    "Contextos rurales diversos",
    "Baja altitud, estructura compleja"
  )
)

print("Tabla resumen ejecutiva:")
print(tabla_ejecutiva_final)

# ===============================================================================
# ESTADÍSTICAS FINALES PARA INFORME
# ===============================================================================

print("\n=== ESTADÍSTICAS FINALES PARA INFORME ===")

# Verificar distribución final
distribucion_verificacion_final <- table(datos_finales$Tipologia_Aprobada)
print("Distribución final verificada:")
print(distribucion_verificacion_final)

# Estadísticas de validación
total_instituciones <- nrow(datos_finales)
silhouette_promedio_final <- round(mean(silhouette_df_final$Silhouette_Value), 3)
instituciones_positivas_final <- sum(silhouette_df_final$Silhouette_Value > 0)
porcentaje_positivas_final <- round((instituciones_positivas_final/total_instituciones) * 100, 1)

cat("\n📊 DATOS FINALES PARA EL INFORME:\n")
cat("• Total de instituciones analizadas:", total_instituciones, "\n")
cat("• Coeficiente Silhouette promedio:", silhouette_promedio_final, "\n")
cat("• Instituciones con asignación correcta:", instituciones_positivas_final, 
    "(", porcentaje_positivas_final, "%)\n")

cat("\n🎯 TIPOLOGÍAS FINALES:\n")
for(i in 1:nrow(tabla_ejecutiva_final)) {
  cat("•", tabla_ejecutiva_final$Tipologia[i], ":", 
      tabla_ejecutiva_final$n[i], "instituciones\n")
}




# ===============================================================================
# VISUALIZACIONES DE CARACTERIZACIÓN ESTADÍSTICA - VERSIÓN CORREGIDA
# Tipologías Institucionales Fe y Alegría - 2025
# ===============================================================================

library(dplyr)
library(ggplot2)
library(gridExtra)
library(reshape2)

# ===============================================================================
# 1. CORRECCIÓN DE TABLA DE MEDIAS
# ===============================================================================

print("=== GENERANDO TABLA DE MEDIAS CORREGIDA ===")

# Extraer solo las medias para tabla resumen (corrigiendo el error anterior)
tabla_medias <- datos_finales %>%
  group_by(Cluster, Tipologia_Aprobada) %>%
  summarise_at(variables_clustering_final, mean, na.rm = TRUE) %>%
  ungroup()

# Mostrar solo las columnas numéricas
tabla_medias_numericas <- tabla_medias[, c(1, 3:ncol(tabla_medias))]
print("Medias por tipología (solo valores numéricos):")
print(round(tabla_medias_numericas, 3))

# Crear tabla transpuesta para mejor visualización
tabla_medias_transpuesta <- as.data.frame(t(tabla_medias[, -c(1:2)]))
colnames(tabla_medias_transpuesta) <- tabla_medias$Tipologia_Aprobada
tabla_medias_transpuesta$Variable <- rownames(tabla_medias_transpuesta)
tabla_medias_transpuesta <- tabla_medias_transpuesta[, c("Variable", colnames(tabla_medias_transpuesta)[1:4])]

print("Tabla de medias transpuesta:")
print(round(tabla_medias_transpuesta[, -1], 3))

# ===============================================================================
# 2. BOXPLOTS DE VARIABLES MÁS DISCRIMINANTES
# ===============================================================================

print("=== GENERANDO BOXPLOTS DE VARIABLES DISCRIMINANTES ===")

# Colores temáticos para gráficos
colores_tipologias <- c(
  "Tradicionales Estables" = "#2980B9",
  "Élite Institucional" = "#F1C40F", 
  "Rurales Resilientes" = "#27AE60",
  "Emergentes Complejas" = "#E67E22"
)

# Función para crear boxplots de las top variables discriminantes
crear_boxplots_discriminantes <- function(datos, variables_top, colores) {
  
  plots_list <- list()
  
  # Nombres más descriptivos para las variables
  nombres_variables <- c(
    "ALTITUD_MSNM" = "Altitud\n(msnm)",
    "X11_RED" = "Ratio\nEst-Docente", 
    "X4_IDD" = "Desempeño\nDocente",
    "X12_TOE" = "Organización\nEscolar",
    "X13_TMATRC" = "Tendencia\nMatrícula",
    "Y1_ILA" = "Logro\nAcadémico"
  )
  
  for(i in 1:min(4, length(variables_top))) {
    variable <- variables_top[i]
    titulo_var <- ifelse(variable %in% names(nombres_variables), 
                         nombres_variables[variable], variable)
    
    p <- ggplot(datos, aes_string(x = "Tipologia_Aprobada", y = variable, 
                                  fill = "Tipologia_Aprobada")) +
      geom_boxplot(alpha = 0.7, outlier.alpha = 0.6, color = "gray30") +
      scale_fill_manual(values = colores) +
      labs(title = titulo_var,
           x = "",
           y = "Valor Estandarizado") +
      theme_minimal() +
      theme(
        axis.text.x = element_text(angle = 45, hjust = 1, size = 8),
        legend.position = "none",
        plot.title = element_text(size = 11, face = "bold", hjust = 0.5),
        panel.grid.major.x = element_blank(),
        panel.grid.minor = element_blank()
      ) +
      geom_hline(yintercept = 0, linetype = "dashed", color = "red", alpha = 0.7)
    
    plots_list[[i]] <- p
  }
  
  return(plots_list)
}

# Variables top sin X2_TR (que tiene discriminación perfecta)
variables_top_graficos <- c("ALTITUD_MSNM", "X11_RED", "X4_IDD", "X12_TOE")

# Generar boxplots
boxplots_discriminantes <- crear_boxplots_discriminantes(
  datos_finales, 
  variables_top_graficos, 
  colores_tipologias
)

# Combinar en panel de 2x2
panel_boxplots <- grid.arrange(
  boxplots_discriminantes[[1]], boxplots_discriminantes[[2]],
  boxplots_discriminantes[[3]], boxplots_discriminantes[[4]],
  ncol = 2, nrow = 2,
  top = "Variables con Mayor Poder Discriminante entre Tipologías"
)

print("Panel de boxplots generado exitosamente")








# ===============================================================================
# HEATMAP CON NÚMEROS PARA TIPOLOGÍAS (1, 2, 3, 4)
# Solución para nombres extensos que se recortan
# ===============================================================================

crear_heatmap_con_numeros <- function(tabla_medias) {
  
  # Preparar datos para heatmap
  datos_heatmap <- tabla_medias[, -c(1:2)]
  
  # Estandarizar por variable (z-score por columnas)
  datos_estandarizados <- scale(datos_heatmap)
  
  # Asignar números como nombres de filas
  rownames(datos_estandarizados) <- c("1", "2", "3", "4")
  
  # Calcular promedio de Z-scores por variable para ordenamiento
  promedios_z <- colMeans(datos_estandarizados)
  orden_variables <- names(sort(promedios_z, decreasing = TRUE))
  
  # Convertir a formato largo para ggplot
  datos_melt <- melt(datos_estandarizados)
  colnames(datos_melt) <- c("Tipologia_Num", "Variable", "Valor_Z")
  
  # Nombres descriptivos para variables
  nombres_variables <- c(
    "Y1_ILA" = "Logro Académico",
    "Y2_TD" = "Tendencia Desempeño", 
    "X1_NVC" = "Vulnerabilidad Contextual",
    "X2_TR" = "Tipo Ruralidad",
    "X4_IDD" = "Desempeño Docente",
    "X11_RED" = "Ratio Estudiante-Docente", 
    "X12_TOE" = "Organización Escolar",
    "X13_TMATRC" = "Tendencia Matrícula",
    "X14_NIVEL_EDUCATIVO" = "Nivel Educativo",
    "ALTITUD_MSNM" = "Altitud Geográfica"
  )
  
  # Aplicar nombres descriptivos
  datos_melt$Variable_Desc <- nombres_variables[as.character(datos_melt$Variable)]
  
  # Crear el orden de variables descriptivas
  orden_descriptivas <- nombres_variables[orden_variables]
  datos_melt$Variable_Desc <- factor(datos_melt$Variable_Desc, 
                                     levels = rev(orden_descriptivas))
  
  # Asegurar que Tipologia_Num sea factor en el orden correcto
  datos_melt$Tipologia_Num <- factor(datos_melt$Tipologia_Num, levels = c("1", "2", "3", "4"))
  
  # Crear heatmap con números
  heatmap_plot <- ggplot(datos_melt, aes(x = Tipologia_Num, y = Variable_Desc, fill = Valor_Z)) +
    geom_tile(color = "white", size = 1.2) +
    scale_fill_gradient2(low = "#D32F2F", high = "#1976D2", mid = "white", 
                         midpoint = 0, limit = c(-2.5, 2.5),
                         name = "Z-Score\n", 
                         breaks = c(-2, -1, 0, 1, 2),
                         labels = c("≤-2", "-1", "0", "+1", "≥+2"),
                         guide = guide_colorbar(
                           title.position = "top",
                           title.hjust = 0.5,
                           barwidth = 1,
                           barheight = 8
                         )) +
    labs(title = "Perfiles Institucionales por Tipología",
         subtitle = "Variables ordenadas por desempeño promedio",
         x = "Tipología (1=Tradicionales | 2=Élite | 3=Rurales | 4=Emergentes)",
         y = "Dimensiones de Caracterización",
         caption = "Azul = Superior al promedio | Rojo = Inferior al promedio | 2025") +
    theme_minimal() +
    theme(
      axis.text.x = element_text(angle = 0, hjust = 0.5, size = 14, face = "bold"),  # Números más grandes
      axis.text.y = element_text(size = 10, hjust = 1),
      plot.title = element_text(size = 15, face = "bold", hjust = 0.5),
      plot.subtitle = element_text(size = 12, hjust = 0.5, color = "gray40"),
      plot.caption = element_text(size = 10, color = "gray50"),
      axis.title.x = element_text(size = 10, face = "bold"),  # Título X más pequeño para que quepa
      legend.position = "right",
      legend.title = element_text(size = 11, face = "bold"),
      legend.text = element_text(size = 10),
      panel.grid = element_blank(),
      axis.title = element_text(size = 12, face = "bold"),
      axis.title.y = element_text(margin = margin(r = 15)),
      plot.margin = margin(20, 25, 20, 20)
    )
  
  return(heatmap_plot)
}

# ===============================================================================
# TABLA DE REFERENCIA PARA ACOMPAÑAR EL GRÁFICO
# ===============================================================================

crear_tabla_referencia_tipologias <- function() {
  
  # Crear tabla de referencia clara
  tabla_referencia <- data.frame(
    Numero = c("1", "2", "3", "4"),
    Tipologia = c("Tradicionales Estables", "Élite Institucional", 
                  "Rurales Resilientes", "Emergentes Complejas"),
    n_Instituciones = c("77 (47.2%)", "7 (4.3%)", "50 (30.7%)", "29 (17.8%)"),
    Caracteristica_Principal = c(
      "Núcleo consolidado de la red",
      "Referentes de excelencia educativa", 
      "Instituciones de contextos andinos",
      "Centros en expansión organizativa"
    )
  )
  
  return(tabla_referencia)
}

# ===============================================================================
# EJECUCIÓN
# ===============================================================================

print("=== GENERANDO HEATMAP CON NÚMEROS PARA TIPOLOGÍAS ===")

# Generar heatmap con números
heatmap_numeros <- crear_heatmap_con_numeros(tabla_medias)
print("Heatmap con tipologías numeradas:")
print(heatmap_numeros)

# Generar tabla de referencia
tabla_ref <- crear_tabla_referencia_tipologias()
print("\nTabla de referencia de tipologías:")
print(tabla_ref)

# Mostrar el orden de variables resultante
datos_heatmap_orden <- tabla_medias[, -c(1:2)]
datos_estandarizados_orden <- scale(datos_heatmap_orden)
promedios_z_orden <- colMeans(datos_estandarizados_orden)
orden_final_orden <- sort(promedios_z_orden, decreasing = TRUE)

print("\nOrden de variables en el heatmap (de arriba hacia abajo):")
nombres_variables_orden <- c(
  "Y1_ILA" = "Logro Académico",
  "Y2_TD" = "Tendencia Desempeño", 
  "X1_NVC" = "Vulnerabilidad Contextual",
  "X2_TR" = "Tipo Ruralidad",
  "X4_IDD" = "Desempeño Docente",
  "X11_RED" = "Ratio Estudiante-Docente", 
  "X12_TOE" = "Organización Escolar",
  "X13_TMATRC" = "Tendencia Matrícula",
  "X14_NIVEL_EDUCATIVO" = "Nivel Educativo",
  "ALTITUD_MSNM" = "Altitud Geográfica"
)

for(i in 1:length(orden_final_orden)) {
  variable_codigo <- names(orden_final_orden)[i]
  variable_nombre <- nombres_variables_orden[variable_codigo]
  promedio_z <- round(orden_final_orden[i], 3)
  cat(i, ".", variable_nombre, "(Z promedio =", promedio_z, ")\n")
}

print("\n=== HEATMAP CON NÚMEROS GENERADO EXITOSAMENTE ===")
print("Ventajas: Números 1-4 son claros y no se recortan")
print("La referencia completa está en el título del eje X y en la tabla de referencia")












# ===============================================================================
# 4. GRÁFICO DE RADAR SIMPLIFICADO (SIN LIBRERÍA EXTERNA)
# ===============================================================================

print("=== GENERANDO GRÁFICO DE RADAR SIMPLIFICADO ===")

# Crear gráfico de radar usando ggplot (alternativa sin fmsb)
crear_radar_ggplot <- function(tabla_medias, variables_principales) {
  
  # Seleccionar variables principales para el radar
  vars_radar <- c("Y1_ILA", "X4_IDD", "X11_RED", "ALTITUD_MSNM", "X13_TMATRC")
  
  # Preparar datos
  datos_radar <- tabla_medias[, c("Tipologia_Aprobada", vars_radar)]
  
  # Convertir a formato largo
  datos_radar_long <- melt(datos_radar, id.vars = "Tipologia_Aprobada")
  colnames(datos_radar_long) <- c("Tipologia", "Variable", "Valor")
  
  # Coordenadas polares simuladas
  n_vars <- length(vars_radar)
  angulos <- seq(0, 2*pi, length.out = n_vars + 1)[1:n_vars]
  
  # Añadir ángulos
  datos_radar_long$Angulo <- rep(angulos, 4)
  
  # Convertir a coordenadas cartesianas
  datos_radar_long$x <- datos_radar_long$Valor * cos(datos_radar_long$Angulo)
  datos_radar_long$y <- datos_radar_long$Valor * sin(datos_radar_long$Angulo)
  
  # Crear gráfico polar alternativo con coordenadas
  radar_plot <- ggplot(datos_radar_long, aes(x = Angulo, y = Valor, 
                                             color = Tipologia, group = Tipologia)) +
    geom_line(size = 1.2, alpha = 0.8) +
    geom_point(size = 3, alpha = 0.9) +
    coord_polar() +
    scale_color_manual(values = colores_tipologias) +
    scale_x_continuous(breaks = angulos, 
                       labels = c("Logro\nAcadémico", "Desempeño\nDocente", 
                                  "Ratio\nEst-Doc", "Altitud", "Tendencia\nMatrícula")) +
    labs(title = "Perfil Multivariado por Tipología",
         subtitle = "Comparación en cinco dimensiones clave",
         color = "Tipología",
         caption = "Valores estandarizados (Z-scores)") +
    theme_minimal() +
    theme(
      plot.title = element_text(size = 14, face = "bold", hjust = 0.5),
      plot.subtitle = element_text(size = 12, hjust = 0.5, color = "gray40"),
      axis.text.y = element_text(size = 8),
      axis.text.x = element_text(size = 9, face = "bold"),
      legend.position = "bottom",
      legend.title = element_text(size = 10, face = "bold"),
      panel.grid.minor = element_blank()
    )
  
  return(radar_plot)
}

# Generar gráfico radar
radar_perfiles <- crear_radar_ggplot(tabla_medias, variables_top_graficos)
print(radar_perfiles)

# ===============================================================================
# 5. PANEL COMBINADO PARA INFORME
# ===============================================================================

print("=== GENERANDO PANEL COMBINADO FINAL ===")

# Panel superior: Heatmap
# Panel inferior: Boxplots (ya combinados)
panel_caracterizacion_completo <- grid.arrange(
  heatmap_perfiles,
  panel_boxplots,
  ncol = 1, nrow = 2,
  heights = c(1.2, 1)
)

print("Panel de caracterización estadística completo generado")

# ===============================================================================
# 6. TABLA RESUMIDA PARA EL INFORME
# ===============================================================================

print("=== TABLA RESUMIDA PARA INFORME ===")

# Crear tabla resumida con las variables más importantes
tabla_resumen_informe <- data.frame(
  Variable = c("Altitud (ALTITUD_MSNM)", "Ratio Est-Docente (X11_RED)", 
               "Desempeño Docente (X4_IDD)", "Logro Académico (Y1_ILA)"),
  Tradicionales = round(c(tabla_medias$ALTITUD_MSNM[1], tabla_medias$X11_RED[1], 
                          tabla_medias$X4_IDD[1], tabla_medias$Y1_ILA[1]), 2),
  Elite = round(c(tabla_medias$ALTITUD_MSNM[2], tabla_medias$X11_RED[2], 
                  tabla_medias$X4_IDD[2], tabla_medias$Y1_ILA[2]), 2),
  Rurales = round(c(tabla_medias$ALTITUD_MSNM[3], tabla_medias$X11_RED[3], 
                    tabla_medias$X4_IDD[3], tabla_medias$Y1_ILA[3]), 2),
  Emergentes = round(c(tabla_medias$ALTITUD_MSNM[4], tabla_medias$X11_RED[4], 
                       tabla_medias$X4_IDD[4], tabla_medias$Y1_ILA[4]), 2)
)

print("Tabla resumen para el informe:")
print(tabla_resumen_informe)

print("\n=== VISUALIZACIONES DE CARACTERIZACIÓN COMPLETADAS ===")
print("Gráficos generados:")
print("1. Panel de boxplots de variables discriminantes")
print("2. Heatmap de perfiles estandarizados") 
print("3. Gráfico radar de perfiles multivariados")
print("4. Panel combinado para informe")
print("5. Tabla resumen ejecutiva")






















# ===============================================================================
# ANÁLISIS DE VARIABLES CONTEXTUALES COMPLEMENTARIAS
# Enriquecimiento del análisis de tipologías institucionales
# ===============================================================================

library(ggplot2)
library(dplyr)
library(reshape2)
library(gridExtra)

print("=== INICIANDO ANÁLISIS DE VARIABLES CONTEXTUALES COMPLEMENTARIAS ===")

# ===============================================================================
# 1. DEFINICIÓN DE VARIABLES CONTEXTUALES POR CATEGORÍAS
# ===============================================================================

# Variables académicas adicionales
variables_academicas_adicionales <- c("Y3_PR")

# Variables de recursos humanos y gestión
variables_recursos_humanos <- c("X5_ED", "X6_CDD", "X20_DIRECTIVOS_TOTAL")

# Variables de equipamiento e infraestructura
variables_equipamiento <- c("X10_IE")

# Variables de modalidad y organización educativa
variables_modalidad_organizacion <- c("X16_MODALIDAD", "X17_GESTION", "X18_TURNO", 
                                      "X19_ORGANIZACION_PEDAGOGICA", "X15_MEIB")

# Variables de multiplicidad y complejidad
variables_multiplicidad <- c("X21_MULTIPLICIDAD1", "X22_MULTIPLICIDAD2")

# Variables geográficas y demográficas
variables_geograficas_demograficas <- c("LATITUD", "LONGITUD", "X24_GPMD", "X25_POBLACION_DISTRITO")

# Compilar todas las variables contextuales
variables_contextuales_todas <- c(
  variables_academicas_adicionales,
  variables_recursos_humanos,
  variables_equipamiento,
  variables_modalidad_organizacion,
  variables_multiplicidad,
  variables_geograficas_demograficas
)

print("Variables contextuales identificadas:")
print(paste("Total de variables adicionales:", length(variables_contextuales_todas)))

# ===============================================================================
# 2. CREAR DATASET CONTEXTUAL ENRIQUECIDO
# ===============================================================================

crear_dataset_contextual_enriquecido <- function() {
  
  # Verificar disponibilidad de variables
  variables_disponibles <- intersect(variables_contextuales_todas, colnames(datos_raw))
  variables_faltantes <- setdiff(variables_contextuales_todas, colnames(datos_raw))
  
  print("Variables contextuales disponibles:")
  print(variables_disponibles)
  
  if(length(variables_faltantes) > 0) {
    print("Variables no disponibles en el dataset:")
    print(variables_faltantes)
  }
  
  # Crear dataset contextual con variables disponibles
  dataset_contextual <- datos_raw %>%
    select(CODIGO_MODULAR, NOMBRE_INSTITUCION, 
           all_of(variables_disponibles)) %>%
    left_join(
      datos_finales %>% select(CODIGO_MODULAR, Cluster, Tipologia_Aprobada),
      by = "CODIGO_MODULAR"
    )
  
  return(list(
    datos = dataset_contextual,
    variables_disponibles = variables_disponibles,
    variables_faltantes = variables_faltantes
  ))
}

# ===============================================================================
# 3. ANÁLISIS DESCRIPTIVO DE VARIABLES CATEGÓRICAS
# ===============================================================================

analizar_variables_categoricas <- function(dataset_contextual) {
  
  datos <- dataset_contextual$datos
  variables_disp <- dataset_contextual$variables_disponibles
  
  # Identificar variables categóricas
  variables_categoricas <- c("X16_MODALIDAD", "X17_GESTION", "X18_TURNO", 
                             "X19_ORGANIZACION_PEDAGOGICA", "X15_MEIB", "X24_GPMD")
  
  variables_cat_disponibles <- intersect(variables_categoricas, variables_disp)
  
  resultados_categoricas <- list()
  
  for(var in variables_cat_disponibles) {
    if(var %in% colnames(datos)) {
      tabla_contingencia <- datos %>%
        count(Tipologia_Aprobada, !!sym(var)) %>%
        group_by(Tipologia_Aprobada) %>%
        mutate(
          porcentaje = round(n / sum(n) * 100, 1),
          total_tipologia = sum(n)
        ) %>%
        ungroup()
      
      resultados_categoricas[[var]] <- tabla_contingencia
    }
  }
  
  return(resultados_categoricas)
}

# ===============================================================================
# 4. ANÁLISIS DESCRIPTIVO DE VARIABLES NUMÉRICAS
# ===============================================================================

analizar_variables_numericas <- function(dataset_contextual) {
  
  datos <- dataset_contextual$datos
  variables_disp <- dataset_contextual$variables_disponibles
  
  # Identificar variables numéricas
  variables_numericas <- c("Y3_PR", "X5_ED", "X6_CDD", "X10_IE", "X20_DIRECTIVOS_TOTAL",
                           "X21_MULTIPLICIDAD1", "X22_MULTIPLICIDAD2", 
                           "LATITUD", "LONGITUD", "X25_POBLACION_DISTRITO")
  
  variables_num_disponibles <- intersect(variables_numericas, variables_disp)
  
  if(length(variables_num_disponibles) > 0) {
    estadisticas_numericas <- datos %>%
      group_by(Cluster, Tipologia_Aprobada) %>%
      summarise(
        across(all_of(variables_num_disponibles), 
               list(
                 promedio = ~round(mean(., na.rm = TRUE), 3),
                 mediana = ~round(median(., na.rm = TRUE), 3),
                 desv_std = ~round(sd(., na.rm = TRUE), 3),
                 minimo = ~round(min(., na.rm = TRUE), 3),
                 maximo = ~round(max(., na.rm = TRUE), 3),
                 n_validos = ~sum(!is.na(.))
               ), .names = "{.col}_{.fn}"),
        .groups = 'drop'
      )
  } else {
    estadisticas_numericas <- NULL
  }
  
  return(estadisticas_numericas)
}

# ===============================================================================
# 5. CARACTERIZACIÓN ESPECÍFICA POR DIMENSIONES
# ===============================================================================

caracterizar_dimension_recursos_humanos <- function(dataset_contextual) {
  
  datos <- dataset_contextual$datos
  
  # Variables de recursos humanos disponibles
  vars_rrhh <- intersect(c("X5_ED", "X6_CDD", "X20_DIRECTIVOS_TOTAL"), 
                         dataset_contextual$variables_disponibles)
  
  if(length(vars_rrhh) > 0) {
    caracterizacion_rrhh <- datos %>%
      group_by(Tipologia_Aprobada) %>%
      summarise(
        n_instituciones = n(),
        across(all_of(vars_rrhh), 
               list(
                 promedio = ~round(mean(., na.rm = TRUE), 2),
                 mediana = ~round(median(., na.rm = TRUE), 2)
               ), .names = "{.col}_{.fn}"),
        .groups = 'drop'
      )
    
    return(caracterizacion_rrhh)
  } else {
    return(NULL)
  }
}

caracterizar_dimension_organizacional <- function(dataset_contextual) {
  
  datos <- dataset_contextual$datos
  
  # Análisis de modalidades educativas
  if("X16_MODALIDAD" %in% colnames(datos)) {
    modalidades <- datos %>%
      count(Tipologia_Aprobada, X16_MODALIDAD) %>%
      group_by(Tipologia_Aprobada) %>%
      mutate(porcentaje = round(n / sum(n) * 100, 1)) %>%
      ungroup() %>%
      arrange(Tipologia_Aprobada, desc(n))
  } else {
    modalidades <- NULL
  }
  
  # Análisis de turnos
  if("X18_TURNO" %in% colnames(datos)) {
    turnos <- datos %>%
      count(Tipologia_Aprobada, X18_TURNO) %>%
      group_by(Tipologia_Aprobada) %>%
      mutate(porcentaje = round(n / sum(n) * 100, 1)) %>%
      ungroup()
  } else {
    turnos <- NULL
  }
  
  # Análisis de gestión
  if("X17_GESTION" %in% colnames(datos)) {
    gestion <- datos %>%
      count(Tipologia_Aprobada, X17_GESTION) %>%
      group_by(Tipologia_Aprobada) %>%
      mutate(porcentaje = round(n / sum(n) * 100, 1)) %>%
      ungroup()
  } else {
    gestion <- NULL
  }
  
  return(list(
    modalidades = modalidades,
    turnos = turnos,
    gestion = gestion
  ))
}

caracterizar_dimension_geografica_demografica <- function(dataset_contextual) {
  
  datos <- dataset_contextual$datos
  
  # Variables geográficas y demográficas
  vars_geo_demo <- intersect(c("LATITUD", "LONGITUD", "X25_POBLACION_DISTRITO"), 
                             dataset_contextual$variables_disponibles)
  
  if(length(vars_geo_demo) > 0) {
    caracterizacion_geo <- datos %>%
      group_by(Tipologia_Aprobada) %>%
      summarise(
        across(all_of(vars_geo_demo), 
               list(
                 promedio = ~round(mean(., na.rm = TRUE), 3),
                 mediana = ~round(median(., na.rm = TRUE), 3),
                 min = ~round(min(., na.rm = TRUE), 3),
                 max = ~round(max(., na.rm = TRUE), 3)
               ), .names = "{.col}_{.fn}"),
        .groups = 'drop'
      )
    
    return(caracterizacion_geo)
  } else {
    return(NULL)
  }
}

# ===============================================================================
# 6. VISUALIZACIONES CONTEXTUALES
# ===============================================================================

crear_visualizaciones_contextuales <- function(dataset_contextual, analisis_categoricas) {
  
  colores_tipologias <- c(
    "Tradicionales Estables" = "#2980B9",
    "Élite Institucional" = "#F1C40F", 
    "Rurales Resilientes" = "#27AE60",
    "Emergentes Complejas" = "#E67E22"
  )
  
  graficos <- list()
  
  # Gráfico 1: Distribución de modalidades (si está disponible)
  if("X16_MODALIDAD" %in% names(analisis_categoricas)) {
    datos_modalidad <- analisis_categoricas$X16_MODALIDAD
    
    grafico_modalidades <- ggplot(datos_modalidad, 
                                  aes(x = X16_MODALIDAD, y = n, fill = Tipologia_Aprobada)) +
      geom_col(position = "dodge", alpha = 0.8) +
      geom_text(aes(label = paste0(n, "\n(", porcentaje, "%)")), 
                position = position_dodge(width = 0.9), vjust = -0.5, size = 3) +
      scale_fill_manual(values = colores_tipologias) +
      labs(title = "Distribución por Modalidad Educativa",
           subtitle = "Características organizativas por tipología",
           x = "Modalidad Educativa", 
           y = "Número de Instituciones",
           fill = "Tipología") +
      theme_minimal() +
      theme(
        plot.title = element_text(size = 14, face = "bold", hjust = 0.5),
        plot.subtitle = element_text(size = 11, hjust = 0.5, color = "gray40"),
        legend.position = "bottom",
        axis.text.x = element_text(angle = 45, hjust = 1)
      )
    
    graficos$modalidades <- grafico_modalidades
  }
  
  # Gráfico 2: Distribución de turnos (si está disponible)
  if("X18_TURNO" %in% names(analisis_categoricas)) {
    datos_turno <- analisis_categoricas$X18_TURNO
    
    grafico_turnos <- ggplot(datos_turno, 
                             aes(x = X18_TURNO, y = n, fill = Tipologia_Aprobada)) +
      geom_col(position = "dodge", alpha = 0.8) +
      geom_text(aes(label = paste0(n, "\n(", porcentaje, "%)")), 
                position = position_dodge(width = 0.9), vjust = -0.5, size = 3) +
      scale_fill_manual(values = colores_tipologias) +
      labs(title = "Distribución por Turno de Funcionamiento",
           subtitle = "Organización temporal por tipología",
           x = "Turno", 
           y = "Número de Instituciones",
           fill = "Tipología") +
      theme_minimal() +
      theme(
        plot.title = element_text(size = 14, face = "bold", hjust = 0.5),
        plot.subtitle = element_text(size = 11, hjust = 0.5, color = "gray40"),
        legend.position = "bottom"
      )
    
    graficos$turnos <- grafico_turnos
  }
  
  return(graficos)
}

# ===============================================================================
# 7. FUNCIÓN PRINCIPAL DE ANÁLISIS CONTEXTUAL
# ===============================================================================

ejecutar_analisis_contextual_completo <- function() {
  
  print("1. Creando dataset contextual enriquecido...")
  dataset_contextual <- crear_dataset_contextual_enriquecido()
  
  print("2. Analizando variables categóricas...")
  analisis_categoricas <- analizar_variables_categoricas(dataset_contextual)
  
  print("3. Analizando variables numéricas...")
  analisis_numericas <- analizar_variables_numericas(dataset_contextual)
  
  print("4. Caracterizando dimensión de recursos humanos...")
  caracterizacion_rrhh <- caracterizar_dimension_recursos_humanos(dataset_contextual)
  
  print("5. Caracterizando dimensión organizacional...")
  caracterizacion_organizacional <- caracterizar_dimension_organizacional(dataset_contextual)
  
  print("6. Caracterizando dimensión geográfica-demográfica...")
  caracterizacion_geo_demo <- caracterizar_dimension_geografica_demografica(dataset_contextual)
  
  print("7. Creando visualizaciones contextuales...")
  visualizaciones <- crear_visualizaciones_contextuales(dataset_contextual, analisis_categoricas)
  
  resultados_contextuales <- list(
    dataset_base = dataset_contextual,
    variables_categoricas = analisis_categoricas,
    variables_numericas = analisis_numericas,
    recursos_humanos = caracterizacion_rrhh,
    organizacional = caracterizacion_organizacional,
    geografica_demografica = caracterizacion_geo_demo,
    visualizaciones = visualizaciones
  )
  
  print("=== ANÁLISIS CONTEXTUAL COMPLETADO EXITOSAMENTE ===")
  return(resultados_contextuales)
}

# ===============================================================================
# 8. FUNCIÓN DE SÍNTESIS POR TIPOLOGÍA
# ===============================================================================

generar_sintesis_contextual_por_tipologia <- function(resultados_contextuales) {
  
  print("=== GENERANDO SÍNTESIS CONTEXTUAL POR TIPOLOGÍA ===")
  
  tipologias <- c("Tradicionales Estables", "Élite Institucional", 
                  "Rurales Resilientes", "Emergentes Complejas")
  
  sintesis_completa <- list()
  
  for(tipologia in tipologias) {
    cat("\n>>> SÍNTESIS CONTEXTUAL:", toupper(tipologia), "<<<\n")
    
    sintesis_tipologia <- list()
    
    # Características organizacionales
    if(!is.null(resultados_contextuales$organizacional$modalidades)) {
      modalidad_principal <- resultados_contextuales$organizacional$modalidades %>%
        filter(Tipologia_Aprobada == tipologia) %>%
        arrange(desc(n)) %>%
        slice(1)
      
      if(nrow(modalidad_principal) > 0) {
        cat("MODALIDAD EDUCATIVA PREDOMINANTE:", modalidad_principal$X16_MODALIDAD, 
            "(", modalidad_principal$porcentaje, "%)\n")
        sintesis_tipologia$modalidad_principal <- modalidad_principal
      }
    }
    
    # Características de recursos humanos
    if(!is.null(resultados_contextuales$recursos_humanos)) {
      rrhh_data <- resultados_contextuales$recursos_humanos %>%
        filter(Tipologia_Aprobada == tipologia)
      
      if(nrow(rrhh_data) > 0) {
        cat("RECURSOS HUMANOS:\n")
        if("X20_DIRECTIVOS_TOTAL_promedio" %in% colnames(rrhh_data)) {
          cat("  • Personal directivo promedio:", rrhh_data$X20_DIRECTIVOS_TOTAL_promedio, "\n")
        }
        sintesis_tipologia$recursos_humanos <- rrhh_data
      }
    }
    
    # Características geográficas-demográficas
    if(!is.null(resultados_contextuales$geografica_demografica)) {
      geo_data <- resultados_contextuales$geografica_demografica %>%
        filter(Tipologia_Aprobada == tipologia)
      
      if(nrow(geo_data) > 0) {
        cat("CONTEXTO GEOGRÁFICO-DEMOGRÁFICO:\n")
        if("X25_POBLACION_DISTRITO_promedio" %in% colnames(geo_data)) {
          cat("  • Población distrito promedio:", format(geo_data$X25_POBLACION_DISTRITO_promedio, big.mark = ","), "\n")
        }
        sintesis_tipologia$geografica_demografica <- geo_data
      }
    }
    
    sintesis_completa[[tipologia]] <- sintesis_tipologia
  }
  
  return(sintesis_completa)
}

# ===============================================================================
# EJECUCIÓN DEL ANÁLISIS CONTEXTUAL
# ===============================================================================

# Ejecutar análisis contextual completo
print("Iniciando análisis contextual enriquecido...")
resultados_contextuales <- ejecutar_analisis_contextual_completo()

# Generar síntesis por tipología
sintesis_tipologias <- generar_sintesis_contextual_por_tipologia(resultados_contextuales)

# Mostrar resumen de variables disponibles
print("\n=== RESUMEN DE VARIABLES CONTEXTUALES DISPONIBLES ===")
print(paste("Variables disponibles:", length(resultados_contextuales$dataset_base$variables_disponibles)))
print("Variables disponibles:")
print(resultados_contextuales$dataset_base$variables_disponibles)

if(length(resultados_contextuales$dataset_base$variables_faltantes) > 0) {
  print("\nVariables no disponibles en el dataset:")
  print(resultados_contextuales$dataset_base$variables_faltantes)
}

# Mostrar análisis de variables categóricas
print("\n=== ANÁLISIS DE VARIABLES CATEGÓRICAS ===")
for(variable in names(resultados_contextuales$variables_categoricas)) {
  cat("\n--- VARIABLE:", variable, "---\n")
  print(resultados_contextuales$variables_categoricas[[variable]])
}

# Mostrar análisis de variables numéricas (si están disponibles)
if(!is.null(resultados_contextuales$variables_numericas)) {
  print("\n=== ESTADÍSTICAS DE VARIABLES NUMÉRICAS ===")
  print(resultados_contextuales$variables_numericas)
}

# Mostrar caracterización de recursos humanos
if(!is.null(resultados_contextuales$recursos_humanos)) {
  print("\n=== CARACTERIZACIÓN DE RECURSOS HUMANOS ===")
  print(resultados_contextuales$recursos_humanos)
}

# Mostrar gráficos disponibles
print("\n=== VISUALIZACIONES CONTEXTUALES DISPONIBLES ===")
if(length(resultados_contextuales$visualizaciones) > 0) {
  for(grafico in names(resultados_contextuales$visualizaciones)) {
    cat("• Gráfico de", grafico, ": resultados_contextuales$visualizaciones$", grafico, "\n")
  }
} else {
  print("No se generaron visualizaciones (variables categóricas no disponibles)")
}

print("\n=== ANÁLISIS CONTEXTUAL ENRIQUECIDO COMPLETADO ===")
print("Todos los resultados están disponibles en: resultados_contextuales")
print("Síntesis por tipología disponible en: sintesis_tipologias")













# ===============================================================================
# 9. FUNCIÓN PARA EXTRAER INSTITUCIONES POR CLUSTER CON REPRESENTATIVIDAD
# ===============================================================================

extraer_instituciones_por_cluster <- function(datos_finales, datos_raw) {
  
  print("=== EXTRAYENDO INSTITUCIONES POR CLUSTER ===")
  
  # Variables clave para toma de decisiones (simplificadas según solicitud)
  variables_clave <- c("Y1_ILA")
  variables_disponibles <- intersect(variables_clave, colnames(datos_raw))
  
  print(paste("Variables disponibles para clustering:", paste(variables_disponibles, collapse = ", ")))
  
  # Crear dataset completo con información de cluster y nombres
  datos_clustering <- datos_finales %>%
    select(CODIGO_MODULAR, Cluster, Tipologia_Aprobada) %>%
    left_join(
      datos_raw %>% select(CODIGO_MODULAR, NOMBRE_INSTITUCION, all_of(variables_disponibles)), 
      by = "CODIGO_MODULAR"
    ) %>%
    filter(!is.na(Cluster) & !is.na(Y1_ILA))  # Solo instituciones con cluster asignado y datos de ILA
  
  print(paste("Instituciones procesadas:", nrow(datos_clustering)))
  
  # Calcular centroides por cluster
  centroides <- datos_clustering %>%
    group_by(Cluster) %>%
    summarise(
      across(all_of(variables_disponibles), ~mean(., na.rm = TRUE), .names = "centroide_{.col}"),
      .groups = 'drop'
    )
  
  print("Centroides calculados:")
  print(centroides)
  
  # Calcular distancia euclidiana al centroide para cada institución
  calcular_distancia_centroide <- function(fila, centroide_cluster) {
    distancias <- numeric(length(variables_disponibles))
    for(i in seq_along(variables_disponibles)) {
      var <- variables_disponibles[i]
      valor_inst <- as.numeric(fila[[var]])
      valor_centroide <- as.numeric(centroide_cluster[[paste0("centroide_", var)]])
      
      if(!is.na(valor_inst) && !is.na(valor_centroide)) {
        distancias[i] <- (valor_inst - valor_centroide)^2
      } else {
        distancias[i] <- 0  # Si hay NA, no contribuye a la distancia
      }
    }
    return(sqrt(sum(distancias)))
  }
  
  # Agregar distancia al centroide
  instituciones_cluster <- datos_clustering %>%
    left_join(centroides, by = "Cluster") %>%
    rowwise() %>%
    mutate(
      Distancia_Centroide = calcular_distancia_centroide(cur_data(), cur_data())
    ) %>%
    ungroup() %>%
    group_by(Cluster) %>%
    mutate(
      Orden_Representatividad = row_number(Distancia_Centroide),
      N_Instituciones_Cluster = n()
    ) %>%
    ungroup() %>%
    arrange(Cluster, Orden_Representatividad) %>%
    select(
      Nro_Orden = Orden_Representatividad,
      Cluster,
      Tipologia_Aprobada,
      CODIGO_MODULAR,
      NOMBRE_INSTITUCION,
      Y1_ILA,
      Distancia_Centroide,
      N_Instituciones_Cluster
    ) %>%
    mutate(
      Representatividad = case_when(
        Nro_Orden <= 3 ~ "Alta",
        Nro_Orden <= N_Instituciones_Cluster * 0.5 ~ "Media",
        TRUE ~ "Baja"
      )
    )
  
  return(instituciones_cluster)
}

# ===============================================================================
# 10. FUNCIÓN PARA GENERAR RESUMEN EJECUTIVO POR CLUSTER
# ===============================================================================

generar_resumen_ejecutivo_clusters <- function(instituciones_cluster) {
  
  print("=== GENERANDO RESUMEN EJECUTIVO POR CLUSTER ===")
  
  resumen_clusters <- list()
  
  for(cluster_num in sort(unique(instituciones_cluster$Cluster))) {
    
    datos_cluster <- instituciones_cluster %>% filter(Cluster == cluster_num)
    tipologia <- unique(datos_cluster$Tipologia_Aprobada)[1]
    
    cat("\n>>> CLUSTER", cluster_num, "- TIPOLOGÍA:", toupper(tipologia), "<<<\n")
    cat("Total de instituciones:", nrow(datos_cluster), "\n")
    
    # Instituciones más representativas (3 primeras)
    instituciones_top <- datos_cluster %>% 
      slice_head(n = 3) %>%
      select(CODIGO_MODULAR, NOMBRE_INSTITUCION, Y1_ILA, Distancia_Centroide)
    
    cat("\nINSTITUCIONES MÁS REPRESENTATIVAS:\n")
    for(i in 1:nrow(instituciones_top)) {
      cat(sprintf("  %d. %s (Cód: %s) - ILA: %.2f, Distancia: %.3f\n",
                  i,
                  instituciones_top$NOMBRE_INSTITUCION[i],
                  instituciones_top$CODIGO_MODULAR[i],
                  instituciones_top$Y1_ILA[i],
                  instituciones_top$Distancia_Centroide[i]))
    }
    
    # Estadísticas del cluster
    stats_cluster <- datos_cluster %>%
      summarise(
        ILA_promedio = round(mean(Y1_ILA, na.rm = TRUE), 2),
        ILA_min = round(min(Y1_ILA, na.rm = TRUE), 2),
        ILA_max = round(max(Y1_ILA, na.rm = TRUE), 2),
        Distancia_promedio = round(mean(Distancia_Centroide, na.rm = TRUE), 3)
      )
    
    cat("\nESTADÍSTICAS DEL CLUSTER:\n")
    cat("  • ILA promedio:", stats_cluster$ILA_promedio, "(rango:", stats_cluster$ILA_min, "-", stats_cluster$ILA_max, ")\n")
    cat("  • Distancia promedio al centroide:", stats_cluster$Distancia_promedio, "\n")
    
    resumen_clusters[[paste0("Cluster_", cluster_num)]] <- list(
      tipologia = tipologia,
      n_instituciones = nrow(datos_cluster),
      instituciones_top = instituciones_top,
      estadisticas = stats_cluster
    )
  }
  
  return(resumen_clusters)
}

# ===============================================================================
# EJECUCIÓN DE ANÁLISIS DE INSTITUCIONES POR CLUSTER
# ===============================================================================

# Extraer instituciones por cluster
print("Extrayendo instituciones por cluster...")
instituciones_por_cluster <- extraer_instituciones_por_cluster(datos_finales, datos_raw)

# Generar resumen ejecutivo
resumen_ejecutivo_clusters <- generar_resumen_ejecutivo_clusters(instituciones_por_cluster)

# Mostrar tabla disponible
print("\n=== TABLA DE INSTITUCIONES POR CLUSTER DISPONIBLE ===")
print(paste("Total de instituciones procesadas:", nrow(instituciones_por_cluster)))
print("Estructura de la tabla:")
print(colnames(instituciones_por_cluster))
print("\nLa tabla completa está disponible en: instituciones_por_cluster")
print("El resumen ejecutivo está disponible en: resumen_ejecutivo_clusters")

# Mostrar muestra de la tabla
print("\n=== MUESTRA DE LA TABLA (Primeras 10 filas) ===")
print(head(instituciones_por_cluster, 10))




# Ver la tabla completa
View(instituciones_por_cluster)




# ===============================================================================
# EXPORTAR TABLA DE INSTITUCIONES POR CLUSTER A CSV
# ===============================================================================

# Exportar tabla completa
write.csv(instituciones_por_cluster, 
          file = "instituciones_por_cluster_completa.csv", 
          row.names = FALSE, 
          fileEncoding = "UTF-8")

# Verificar exportación exitosa
print(paste("Archivo exportado exitosamente:", getwd(), "/instituciones_por_cluster_completa.csv"))
print(paste("Total de filas exportadas:", nrow(instituciones_por_cluster)))
print(paste("Total de columnas exportadas:", ncol(instituciones_por_cluster)))

# Opcional: Exportar también el resumen ejecutivo por separado
resumen_para_csv <- do.call(rbind, lapply(names(resumen_ejecutivo_clusters), function(cluster_name) {
  cluster_data <- resumen_ejecutivo_clusters[[cluster_name]]
  data.frame(
    Cluster = gsub("Cluster_", "", cluster_name),
    Tipologia = cluster_data$tipologia,
    N_Instituciones = cluster_data$n_instituciones,
    ILA_Promedio = cluster_data$estadisticas$ILA_promedio,
    ILA_Min = cluster_data$estadisticas$ILA_min,
    ILA_Max = cluster_data$estadisticas$ILA_max,
    Distancia_Promedio = cluster_data$estadisticas$Distancia_promedio
  )
}))

write.csv(resumen_para_csv, 
          file = "resumen_ejecutivo_clusters.csv", 
          row.names = FALSE, 
          fileEncoding = "UTF-8")

print("Archivo de resumen ejecutivo también exportado: resumen_ejecutivo_clusters.csv")

















# ===============================================================================
# 11. MATRIZ CUALITATIVA DE TIPOLOGÍAS - CONVERSIÓN Z-SCORES
# ===============================================================================

crear_matriz_cualitativa_tipologias <- function(datos_finales, variables_clustering_final) {
  
  print("=== GENERANDO MATRIZ CUALITATIVA DE TIPOLOGÍAS ===")
  
  # Variables analizadas en el sistema
  variables_sistema <- data.frame(
    Codigo = variables_clustering_final,
    Nombre_Descriptivo = c(
      "Índice de Logro Académico",
      "Tendencia de Desempeño", 
      "Nivel de Vulnerabilidad Contextual",
      "Tipo de Ruralidad",
      "Índice de Desempeño Docente",
      "Ratio Estudiante-Docente",
      "Tipo de Organización Escolar",
      "Tendencia de Matrícula",
      "Nivel Educativo",
      "Altitud Geográfica"
    ),
    Escala = c(
      "1.0 - 4.0", "Variable continua", "1-5 (quintil invertido)", 
      "1-4 (ordinal)", "1.0 - 4.0", "2.0 - 45.0", "1-4 (categórica)",
      "Variable continua", "1-9 (ordinal)", "Metros s.n.m."
    )
  )
  
  print("Variables del sistema de análisis:")
  print(variables_sistema)
  
  # Calcular medias por tipología
  medias_tipologias <- datos_finales %>%
    group_by(Tipologia_Aprobada) %>%
    summarise(
      across(all_of(variables_clustering_final), ~mean(., na.rm = TRUE)),
      .groups = 'drop'
    )
  
  # Transponer para tener variables en filas
  matriz_medias <- as.data.frame(t(medias_tipologias[, -1]))
  colnames(matriz_medias) <- medias_tipologias$Tipologia_Aprobada
  matriz_medias$Variable <- rownames(matriz_medias)
  
  # Estandarizar por variable (Z-score por filas)
  matriz_z_scores <- matriz_medias[, 1:4]  # Solo las columnas de tipologías
  
  # Calcular Z-scores por variable (fila)
  for(i in 1:nrow(matriz_z_scores)) {
    valores_fila <- as.numeric(matriz_z_scores[i, ])
    media_fila <- mean(valores_fila, na.rm = TRUE)
    sd_fila <- sd(valores_fila, na.rm = TRUE)
    
    if(sd_fila > 0) {
      matriz_z_scores[i, ] <- (valores_fila - media_fila) / sd_fila
    } else {
      matriz_z_scores[i, ] <- 0  # Si no hay variación, asignar 0
    }
  }
  
  # Función para convertir Z-scores a categorías
  z_to_cualitativo <- function(z_score) {
    case_when(
      z_score < -0.5 ~ "Bajo",
      z_score >= -0.5 & z_score <= 0.5 ~ "Medio", 
      z_score > 0.5 ~ "Alto",
      TRUE ~ "Medio"  # Default para NAs
    )
  }
  
  # Aplicar conversión cualitativa
  matriz_cualitativa <- matriz_z_scores %>%
    mutate(across(everything(), z_to_cualitativo))
  
  # Agregar información de variables
  matriz_cualitativa$Variable <- variables_sistema$Nombre_Descriptivo
  matriz_cualitativa <- matriz_cualitativa[, c("Variable", colnames(matriz_cualitativa)[1:4])]
  
  # Crear versión con Z-scores para referencia
  matriz_z_scores$Variable <- variables_sistema$Nombre_Descriptivo
  matriz_z_scores <- matriz_z_scores[, c("Variable", colnames(matriz_z_scores)[1:4])]
  
  # Redondear Z-scores a 2 decimales
  matriz_z_scores[, 2:5] <- round(matriz_z_scores[, 2:5], 2)
  
  resultados <- list(
    variables_sistema = variables_sistema,
    matriz_cualitativa = matriz_cualitativa,
    matriz_z_scores = matriz_z_scores,
    medias_originales = medias_tipologias
  )
  
  return(resultados)
}

# ===============================================================================
# 12. VISUALIZACIÓN DE LA MATRIZ CUALITATIVA
# ===============================================================================

crear_heatmap_cualitativo <- function(matriz_cualitativa) {
  
  # Preparar datos para visualización
  datos_heatmap <- matriz_cualitativa %>%
    pivot_longer(cols = -Variable, names_to = "Tipologia", values_to = "Nivel") %>%
    mutate(
      Nivel_Num = case_when(
        Nivel == "Bajo" ~ 1,
        Nivel == "Medio" ~ 2, 
        Nivel == "Alto" ~ 3
      ),
      Variable = factor(Variable, levels = rev(matriz_cualitativa$Variable))
    )
  
  # Colores para los niveles
  colores_niveles <- c("Bajo" = "#E74C3C", "Medio" = "#F39C12", "Alto" = "#27AE60")
  
  # Crear heatmap
  heatmap_cualitativo <- ggplot(datos_heatmap, 
                                aes(x = Tipologia, y = Variable, fill = Nivel)) +
    geom_tile(color = "white", size = 1) +
    geom_text(aes(label = Nivel), size = 4, fontface = "bold", color = "white") +
    scale_fill_manual(values = colores_niveles) +
    labs(title = "Matriz Cualitativa de Perfiles Institucionales",
         subtitle = "Caracterización categórica por tipología",
         x = "Tipologías Institucionales",
         y = "Dimensiones de Análisis",
         fill = "Nivel",
         caption = "Basado en Z-scores estandarizados | 2025") +
    theme_minimal() +
    theme(
      plot.title = element_text(size = 15, face = "bold", hjust = 0.5),
      plot.subtitle = element_text(size = 12, hjust = 0.5, color = "gray40"),
      axis.text.x = element_text(angle = 45, hjust = 1, size = 10, face = "bold"),
      axis.text.y = element_text(size = 10),
      legend.position = "right",
      panel.grid = element_blank(),
      plot.caption = element_text(size = 9, color = "gray50")
    )
  
  return(heatmap_cualitativo)
}

# ===============================================================================
# 13. FUNCIÓN DE EXPORTACIÓN
# ===============================================================================

exportar_matrices_tipologias <- function(resultados_matriz) {
  
  # Exportar matriz cualitativa
  write.csv(resultados_matriz$matriz_cualitativa, 
            file = "matriz_cualitativa_tipologias.csv", 
            row.names = FALSE, 
            fileEncoding = "UTF-8")
  
  # Exportar matriz con Z-scores
  write.csv(resultados_matriz$matriz_z_scores, 
            file = "matriz_z_scores_tipologias.csv", 
            row.names = FALSE, 
            fileEncoding = "UTF-8")
  
  # Exportar sistema de variables
  write.csv(resultados_matriz$variables_sistema, 
            file = "sistema_variables_analisis.csv", 
            row.names = FALSE, 
            fileEncoding = "UTF-8")
  
  print("=== MATRICES EXPORTADAS EXITOSAMENTE ===")
  print("Archivos generados:")
  print("• matriz_cualitativa_tipologias.csv")
  print("• matriz_z_scores_tipologias.csv") 
  print("• sistema_variables_analisis.csv")
}

# ===============================================================================
# EJECUCIÓN DE ANÁLISIS CUALITATIVO
# ===============================================================================

# Generar matriz cualitativa
print("Generando análisis cualitativo de tipologías...")
resultados_matriz_cualitativa <- crear_matriz_cualitativa_tipologias(datos_finales, variables_clustering_final)

# Mostrar resultados
print("\n=== SISTEMA DE VARIABLES ANALIZADAS ===")
print(resultados_matriz_cualitativa$variables_sistema)

print("\n=== MATRIZ CUALITATIVA ===")
print(resultados_matriz_cualitativa$matriz_cualitativa)

print("\n=== MATRIZ Z-SCORES (REFERENCIA) ===")
print(resultados_matriz_cualitativa$matriz_z_scores)

# Crear visualización
heatmap_cualitativo <- crear_heatmap_cualitativo(resultados_matriz_cualitativa$matriz_cualitativa)
print("Heatmap cualitativo:")
print(heatmap_cualitativo)

# Exportar matrices
exportar_matrices_tipologias(resultados_matriz_cualitativa)

# Resumen ejecutivo
print("\n=== RESUMEN EJECUTIVO DE LA MATRIZ CUALITATIVA ===")
cat("La matriz cualitativa transforma los valores estandarizados en categorías interpretables:\n")
cat("• BAJO: Z-score < -0.5 (por debajo del promedio del grupo)\n")
cat("• MEDIO: -0.5 ≤ Z-score ≤ 0.5 (cercano al promedio del grupo)\n")
cat("• ALTO: Z-score > 0.5 (por encima del promedio del grupo)\n\n")

# Conteo de características por tipología
for(tipologia in colnames(resultados_matriz_cualitativa$matriz_cualitativa)[2:5]) {
  valores <- resultados_matriz_cualitativa$matriz_cualitativa[[tipologia]]
  conteo <- table(valores)
  cat("TIPOLOGÍA:", tipologia, "\n")
  cat("  • Alto:", conteo["Alto"], "variables\n")
  cat("  • Medio:", conteo["Medio"], "variables\n") 
  cat("  • Bajo:", conteo["Bajo"], "variables\n\n")
}

print("=== ANÁLISIS CUALITATIVO COMPLETADO ===")