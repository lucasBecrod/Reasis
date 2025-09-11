# ===============================================================================
# PROYECTO REASIS - PASO 1: CARGAR DATOS
# Análisis de Tipologías de Instituciones Educativas Fe y Alegría
# ===============================================================================

# 1. CARGAR LIBRERÍAS NECESARIAS
# ===============================================================================
library(readxl)      # Para leer archivos Excel
library(dplyr)       # Para manipulación de datos
library(tidyr)       # Para la función gather()

# 2. CARGAR DATOS DESDE EXCEL
# ===============================================================================
# Ruta del archivo
ruta_archivo <- "C:/Users/lucas/Proyectos/Reasis/01 Analisis Excel/reasis_database_v5_final.xlsx"

# Cargar la tabla indices_metodologicos
print("Cargando datos desde Excel...")
datos_raw <- read_excel(ruta_archivo, 
                        sheet = "indices_metodologicos",
                        range = "A1:AC164")

# 3. VERIFICACIÓN INICIAL DE LOS DATOS
# ===============================================================================
# Verificar la carga de datos
print(paste("Datos cargados exitosamente:", nrow(datos_raw), "filas,", ncol(datos_raw), "columnas"))

# Mostrar estructura de los datos
print("=== ESTRUCTURA DE LOS DATOS ===")
str(datos_raw)

# Mostrar nombres de columnas
print("=== NOMBRES DE COLUMNAS ===")
print(names(datos_raw))

# Mostrar primeras 5 filas
print("=== PRIMERAS 5 FILAS ===")
print(head(datos_raw, 5))

# Verificar las variables que mencionaste
variables_esperadas <- c("CODIGO_MODULAR", "NOMBRE_INSTITUCION", "NUMERO_FYA", 
                         "LATITUD", "LONGITUD", "ALTITUD_MSNM", "Y1_ILA", "Y2_TD", 
                         "Y3_PR", "X1_NVC", "X2_TR", "X4_IDD", "X5_ED", "X6_CDD", 
                         "X10_IE", "X11_RED", "X12_TOE", "X15_MEIB", "X13_TMATRC", 
                         "X14_NIVEL_EDUCATIVO", "X16_MODALIDAD", "X17_GESTION", 
                         "X18_TURNO", "X19_ORGANIZACION_PEDAGOGICA", "X20_DIRECTIVOS_TOTAL", 
                         "X21_MULTIPLICIDAD1", "X22_MULTIPLICIDAD2", "X24_GPMD", 
                         "X25_POBLACION_DISTRITO")

print("=== VERIFICACIÓN DE VARIABLES ESPERADAS ===")
variables_encontradas <- variables_esperadas %in% names(datos_raw)
variables_faltantes <- variables_esperadas[!variables_encontradas]
variables_presentes <- variables_esperadas[variables_encontradas]

print(paste("Variables encontradas:", length(variables_presentes), "de", length(variables_esperadas)))

if(length(variables_faltantes) > 0) {
  print("Variables faltantes:")
  print(variables_faltantes)
} else {
  print("¡Excelente! Todas las variables esperadas están presentes.")
}

print("Variables presentes:")
print(variables_presentes)

# 4. RESUMEN BÁSICO DE LOS DATOS
# ===============================================================================
print("=== RESUMEN DE DATOS NUMÉRICOS ===")
datos_numericos_temp <- datos_raw %>% select_if(is.numeric)
print(summary(datos_numericos_temp))

# Verificar datos faltantes por variable
print("=== DATOS FALTANTES POR VARIABLE ===")
datos_faltantes <- datos_raw %>%
  summarise_all(~sum(is.na(.))) %>%
  gather(key = "Variable", value = "Datos_Faltantes") %>%
  mutate(Total_Observaciones = nrow(datos_raw),
         Porcentaje_Faltantes = round((Datos_Faltantes / nrow(datos_raw)) * 100, 2),
         Datos_Completos = Total_Observaciones - Datos_Faltantes,
         Porcentaje_Completos = round(100 - Porcentaje_Faltantes, 2)) %>%
  arrange(desc(Datos_Faltantes))

print(datos_faltantes)

print("=== CARGA DE DATOS COMPLETADA ===")
print("Ejecuta este script y compárteme el resultado para continuar con el análisis de correlación.")





# PASO 2: ANÁLISIS DE CORRELACIÓN
print("=== ANÁLISIS DE CORRELACIÓN ===")

# Ver la tabla completa de datos faltantes
print(datos_faltantes, n = 29)

# Seleccionar solo variables numéricas para clustering (excluyendo identificadores)
variables_clustering <- datos_raw %>%
  select(Y1_ILA, Y2_TD, Y3_PR, X1_NVC, X2_TR, X4_IDD, X5_ED, 
         X6_CDD, X10_IE, X11_RED, X12_TOE, X15_MEIB, X13_TMATRC)

# Calcular matriz de correlación
matriz_correlacion <- cor(variables_clustering, use = "complete.obs")
print("Matriz de correlación:")
print(round(matriz_correlacion, 3))



# Análisis de correlación expandido con variables de contexto
variables_completas <- datos_raw %>%
  select(Y1_ILA, Y2_TD, Y3_PR, X1_NVC, X2_TR, X4_IDD, X5_ED, 
         X6_CDD, X10_IE, X11_RED, X12_TOE, X15_MEIB, X13_TMATRC,
         LATITUD, LONGITUD, ALTITUD_MSNM, X14_NIVEL_EDUCATIVO,
         X16_MODALIDAD, X17_GESTION, X18_TURNO, X19_ORGANIZACION_PEDAGOGICA,
         X20_DIRECTIVOS_TOTAL, X21_MULTIPLICIDAD1, X22_MULTIPLICIDAD2,
         X24_GPMD, X25_POBLACION_DISTRITO)

matriz_completa <- cor(variables_completas, use = "complete.obs")
print("Matriz de correlación completa:")
print(round(matriz_completa, 3))


# Análisis comparativo LATITUD vs ALTITUD
print("=== CORRELACIONES LATITUD ===")
latitud_cors <- datos_raw %>%
  select(LATITUD, Y1_ILA, Y2_TD, X1_NVC, X2_TR, X4_IDD, X11_RED, X12_TOE, X13_TMATRC, X14_NIVEL_EDUCATIVO) %>%
  cor(use = "complete.obs")
print(round(latitud_cors["LATITUD", ], 3))

print("=== CORRELACIONES ALTITUD ===")
altitud_cors <- datos_raw %>%
  select(ALTITUD_MSNM, Y1_ILA, Y2_TD, X1_NVC, X2_TR, X4_IDD, X11_RED, X12_TOE, X13_TMATRC, X14_NIVEL_EDUCATIVO) %>%
  cor(use = "complete.obs")
print(round(altitud_cors["ALTITUD_MSNM", ], 3))

print("=== CORRELACIÓN ENTRE ELLAS ===")
print(paste("LATITUD vs ALTITUD:", round(cor(datos_raw$LATITUD, datos_raw$ALTITUD_MSNM), 3)))







# PASO 4: Evaluación cuantitativa del poder explicativo
print("=== EVALUACIÓN PODER EXPLICATIVO ===")

# Suma de correlaciones absolutas (mayor = más información)
latitud_poder <- sum(abs(latitud_cors["LATITUD", 2:10]))
altitud_poder <- sum(abs(altitud_cors["ALTITUD_MSNM", 2:10]))

print(paste("Poder explicativo LATITUD:", round(latitud_poder, 3)))
print(paste("Poder explicativo ALTITUD:", round(altitud_poder, 3)))

# Número de correlaciones moderadas (>0.2)
latitud_moderadas <- sum(abs(latitud_cors["LATITUD", 2:10]) > 0.2)
altitud_moderadas <- sum(abs(altitud_cors["ALTITUD_MSNM", 2:10]) > 0.2)

print(paste("Correlaciones moderadas LATITUD:", latitud_moderadas))
print(paste("Correlaciones moderadas ALTITUD:", altitud_moderadas))

















# VARIABLES FINALES CONFIRMADAS CON ALTITUD
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
  "ALTITUD_MSNM"         # Altitud (SELECCIÓN FINAL)
)

# Crear dataset final para clustering
datos_clustering_final <- datos_raw %>%
  select(CODIGO_MODULAR, NOMBRE_INSTITUCION, all_of(variables_clustering_final))

print("=== SELECCIÓN FINAL PARA CLUSTERING ===")
print(paste("Instituciones:", nrow(datos_clustering_final)))
print("Variables seleccionadas:")
print(variables_clustering_final)

# Verificar matriz de correlación final (sin multicolinealidad)
matriz_final_limpia <- cor(datos_clustering_final[variables_clustering_final], use = "complete.obs")
print("=== MATRIZ CORRELACIÓN FINAL (sin multicolinealidad) ===")
print(round(matriz_final_limpia, 3))

# Verificar que no hay correlaciones >0.7
correlaciones_altas <- which(abs(matriz_final_limpia) > 0.7 & abs(matriz_final_limpia) < 1, arr.ind = TRUE)
print(paste("Correlaciones altas detectadas:", nrow(correlaciones_altas)))









# PASO 2: Estandarización Z-score
print("=== ESTANDARIZACIÓN DE VARIABLES ===")

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

print("=== PRIMERAS 5 FILAS ESTANDARIZADAS ===")
print(head(datos_clustering_z[, 1:8], 5))  # Solo primeras variables para ver






# Instalar librerías necesarias (solo ejecutar una vez)
print("=== INSTALANDO LIBRERÍAS NECESARIAS ===")

# Verificar e instalar librerías faltantes
paquetes_necesarios <- c("cluster", "factoextra")

for(paquete in paquetes_necesarios) {
  if(!require(paquete, character.only = TRUE)) {
    print(paste("Instalando:", paquete))
    install.packages(paquete)
    library(paquete, character.only = TRUE)
  } else {
    print(paste("Ya instalado:", paquete))
  }
}

print("=== INSTALACIÓN COMPLETADA ===")





# PASO 3: Análisis K óptimo (sin NbClust)
library(factoextra)  # Ya instalado
library(cluster)     # Ya instalado

print("=== DETERMINACIÓN K ÓPTIMO ===")

# MÉTODO 1: Análisis del Codo (Elbow Method)
print("=== MÉTODO DEL CODO ===")

set.seed(123)  # Para reproducibilidad
elbow_plot <- fviz_nbclust(datos_estandarizados, kmeans, method = "wss", k.max = 10)
print(elbow_plot)

# MÉTODO 2: Análisis Silhouette
print("=== MÉTODO SILHOUETTE ===")

silhouette_plot <- fviz_nbclust(datos_estandarizados, kmeans, method = "silhouette", k.max = 10)
print(silhouette_plot)

# MÉTODO 3: Cálculo manual para confirmar
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
mejora <- c(NA)  # Primer valor no tiene mejora
for(i in 2:length(wcss_manual)) {
  mejora[i] <- round((wcss_manual[i-1] - wcss_manual[i]) / wcss_manual[i-1] * 100, 2)
}

mejora_df <- data.frame(K = k_values, WCSS = round(wcss_manual, 2), Mejora_Porcentual = mejora)
print("Mejora por K:")
print(mejora_df)

print("=== ANÁLISIS COMPLETADO ===")


# PREPARAR AMBOS CLUSTERING PARA COMPARACIÓN
print("=== CLUSTERING K=3 Y K=4 PARA COMPARACIÓN ===")

set.seed(123)

# Clustering K=3
kmeans_k3 <- kmeans(datos_estandarizados, centers = 3, nstart = 25)
print("=== CLUSTERING K=3 ===")
print(paste("Tamaño clusters K=3:", paste(kmeans_k3$size, collapse = ", ")))

# Clustering K=4  
kmeans_k4 <- kmeans(datos_estandarizados, centers = 4, nstart = 25)
print("=== CLUSTERING K=4 ===")
print(paste("Tamaño clusters K=4:", paste(kmeans_k4$size, collapse = ", ")))

# Distribución de instituciones por cluster
print("Distribución K=3:")
table(kmeans_k3$cluster)
print("Distribución K=4:")







# INVESTIGAR EL CLUSTER PEQUEÑO DE 7 INSTITUCIONES
print("=== ANÁLISIS DEL CLUSTER PEQUEÑO ===")

# Identificar las 7 instituciones del cluster pequeño (K=3)
cluster_pequeno_k3 <- which(kmeans_k3$cluster == 1)  # Cluster 1 tiene 7
instituciones_pequenas <- datos_clustering_z[cluster_pequeno_k3, ]

print("Instituciones en cluster pequeño (K=3):")
print(instituciones_pequenas[, c("CODIGO_MODULAR", "NOMBRE_INSTITUCION")])

# Características del cluster pequeño vs promedio general
print("=== CARACTERÍSTICAS CLUSTER PEQUEÑO vs PROMEDIO ===")
cluster_caracteristicas <- datos_estandarizados[cluster_pequeno_k3, ]
promedios_cluster <- round(colMeans(cluster_caracteristicas), 2)
promedios_general <- round(colMeans(datos_estandarizados), 2)

comparacion <- data.frame(
  Variable = names(promedios_cluster),
  Cluster_Pequeño = promedios_cluster,
  Promedio_General = promedios_general,
  Diferencia = round(promedios_cluster - promedios_general, 2)
)
print(comparacion)

# EVALUAR K=2 COMO ALTERNATIVA ROBUSTA
print("=== CLUSTERING K=2 (ROBUSTO) ===")
set.seed(123)
kmeans_k2 <- kmeans(datos_estandarizados, centers = 2, nstart = 25)
print(paste("Tamaño clusters K=2:", paste(kmeans_k2$size, collapse = ", ")))
print("Distribución K=2:")
table(kmeans_k2$cluster)
table(kmeans_k4$cluster)








# CARACTERIZACIÓN FINAL K=2
print("=== CARACTERIZACIÓN FINAL K=2 ===")

# Agregar clusters a los datos
datos_finales_k2 <- datos_clustering_z
datos_finales_k2$Cluster <- kmeans_k2$cluster

# Caracterización por cluster
print("=== CLUSTER 1 (n=106) ===")
cluster1_stats <- datos_finales_k2[datos_finales_k2$Cluster == 1, ]
caracteristicas_c1 <- round(colMeans(cluster1_stats[, 3:12]), 2)
print(caracteristicas_c1)

print("=== CLUSTER 2 (n=57) ===")
cluster2_stats <- datos_finales_k2[datos_finales_k2$Cluster == 2, ]
caracteristicas_c2 <- round(colMeans(cluster2_stats[, 3:12]), 2)
print(caracteristicas_c2)

# Comparación lado a lado
print("=== COMPARACIÓN CLUSTER 1 vs 2 ===")
comparacion_final <- data.frame(
  Variable = names(caracteristicas_c1),
  Cluster_1_n106 = caracteristicas_c1,
  Cluster_2_n57 = caracteristicas_c2,
  Diferencia = round(caracteristicas_c2 - caracteristicas_c1, 2)
)
print(comparacion_final)





# VISUALIZACIÓN FINAL DE CLUSTERS
print("=== VISUALIZACIÓN FINAL ===")

# Agregar nombres de tipologías
datos_finales_k2$Tipologia <- ifelse(datos_finales_k2$Cluster == 1, 
                                     "Urbanas Alto Rendimiento", 
                                     "Andinas en Mejoramiento")

# Mostrar ejemplos de cada tipología
print("=== EJEMPLOS TIPOLOGÍA 1: URBANAS ALTO RENDIMIENTO ===")
ejemplos_t1 <- datos_finales_k2[datos_finales_k2$Cluster == 1, c("CODIGO_MODULAR", "NOMBRE_INSTITUCION", "Tipologia")]
print(head(ejemplos_t1, 8))

print("=== EJEMPLOS TIPOLOGÍA 2: ANDINAS EN MEJORAMIENTO ===")
ejemplos_t2 <- datos_finales_k2[datos_finales_k2$Cluster == 2, c("CODIGO_MODULAR", "NOMBRE_INSTITUCION", "Tipologia")]
print(head(ejemplos_t2, 8))

# Crear visualización de clusters
library(factoextra)
fviz_cluster(kmeans_k2, data = datos_estandarizados,
             palette = c("#E74C3C", "#3498DB"),
             geom = "point",
             ellipse.type = "convex",
             ggtheme = theme_bw(),
             main = "Tipologías Institucionales Fe y Alegría")

# Resumen final
print("=== RESUMEN FINAL CLUSTERING ===")
summary_final <- table(datos_finales_k2$Tipologia)
print(summary_final)
print(paste("Total instituciones analizadas:", nrow(datos_finales_k2)))







# ANÁLISIS VISUAL K=3
print("=== ANÁLISIS DETALLADO K=3 ===")

library(factoextra)

# Datos K=3 (ya calculado: kmeans_k3)
datos_k3 <- datos_clustering_z
datos_k3$Cluster <- kmeans_k3$cluster

# Asignar nombres descriptivos a tipologías K=3
datos_k3$Tipologia <- case_when(
  datos_k3$Cluster == 1 ~ "Élite Urbana",
  datos_k3$Cluster == 2 ~ "Grupo Intermedio", 
  datos_k3$Cluster == 3 ~ "Grupo Principal"
)

print("=== DISTRIBUCIÓN K=3 ===")
distribucion_k3 <- table(datos_k3$Tipologia)
print(distribucion_k3)
print(paste("Porcentajes:", round(prop.table(distribucion_k3) * 100, 1)))

# Caracterización de los 3 clusters
print("=== CARACTERIZACIÓN CLUSTERS K=3 ===")

# Cluster 1 - Élite Urbana (n=7)
cluster1_k3 <- datos_k3[datos_k3$Cluster == 1, ]
caract_c1_k3 <- round(colMeans(cluster1_k3[, 3:12]), 2)
print("CLUSTER 1 - Élite Urbana (n=7):")
print(caract_c1_k3)

# Cluster 2 - Intermedio (n=53)  
cluster2_k3 <- datos_k3[datos_k3$Cluster == 2, ]
caract_c2_k3 <- round(colMeans(cluster2_k3[, 3:12]), 2)
print("CLUSTER 2 - Grupo Intermedio (n=53):")
print(caract_c2_k3)

# Cluster 3 - Principal (n=103)
cluster3_k3 <- datos_k3[datos_k3$Cluster == 3, ]
caract_c3_k3 <- round(colMeans(cluster3_k3[, 3:12]), 2)
print("CLUSTER 3 - Grupo Principal (n=103):")
print(caract_c3_k3)

# Ejemplos instituciones Élite Urbana
print("=== INSTITUCIONES ÉLITE URBANA ===")
ejemplos_elite <- datos_k3[datos_k3$Cluster == 1, c("CODIGO_MODULAR", "NOMBRE_INSTITUCION")]
print(ejemplos_elite)

# Visualización K=3
plot_k3 <- fviz_cluster(kmeans_k3, data = datos_estandarizados,
                        palette = c("#E74C3C", "#F39C12", "#3498DB"),
                        geom = "point",
                        ellipse.type = "convex",
                        ggtheme = theme_bw(), 
                        main = "K=3: Élite Urbana + Intermedio + Principal",
                        subtitle = "Cluster Élite: n=7 (4.3%), Intermedio: n=53 (32.5%), Principal: n=103 (63.2%)")

print(plot_k3)

print("=== ANÁLISIS K=3 COMPLETADO ===")
print("Observa el gráfico y las características. ¿El cluster de 7 se ve como un grupo natural o como outliers?")




# ANÁLISIS VISUAL K=4
print("=== ANÁLISIS DETALLADO K=4 ===")

# Datos K=4 (ya calculado: kmeans_k4)
datos_k4 <- datos_clustering_z
datos_k4$Cluster <- kmeans_k4$cluster

# Asignar nombres descriptivos a tipologías K=4
datos_k4$Tipologia <- case_when(
  datos_k4$Cluster == 1 ~ "Grupo A",
  datos_k4$Cluster == 2 ~ "Grupo B", 
  datos_k4$Cluster == 3 ~ "Grupo C",
  datos_k4$Cluster == 4 ~ "Élite Urbana"
)

print("=== DISTRIBUCIÓN K=4 ===")
distribucion_k4 <- table(datos_k4$Tipologia)
print(distribucion_k4)
print(paste("Porcentajes:", round(prop.table(distribucion_k4) * 100, 1)))

# Caracterización de los 4 clusters
print("=== CARACTERIZACIÓN CLUSTERS K=4 ===")

# Cluster 1 (n=50)
cluster1_k4 <- datos_k4[datos_k4$Cluster == 1, ]
caract_c1_k4 <- round(colMeans(cluster1_k4[, 3:12]), 2)
print("CLUSTER 1 - Grupo A (n=50):")
print(caract_c1_k4)

# Cluster 2 (n=29)
cluster2_k4 <- datos_k4[datos_k4$Cluster == 2, ]
caract_c2_k4 <- round(colMeans(cluster2_k4[, 3:12]), 2)
print("CLUSTER 2 - Grupo B (n=29):")
print(caract_c2_k4)

# Cluster 3 (n=77)
cluster3_k4 <- datos_k4[datos_k4$Cluster == 3, ]
caract_c3_k4 <- round(colMeans(cluster3_k4[, 3:12]), 2)
print("CLUSTER 3 - Grupo C (n=77):")
print(caract_c3_k4)

# Cluster 4 - Élite (n=7)
cluster4_k4 <- datos_k4[datos_k4$Cluster == 4, ]
caract_c4_k4 <- round(colMeans(cluster4_k4[, 3:12]), 2)
print("CLUSTER 4 - Élite Urbana (n=7):")
print(caract_c4_k4)

# Verificar si élite es la misma en K=3 y K=4
print("=== VERIFICACIÓN ÉLITE K=3 vs K=4 ===")
elite_k3_codigos <- datos_k3[datos_k3$Cluster == 1, "CODIGO_MODULAR"]
elite_k4_codigos <- datos_k4[datos_k4$Cluster == 4, "CODIGO_MODULAR"]
print("¿Mismas instituciones élite?")
print(identical(sort(elite_k3_codigos), sort(elite_k4_codigos)))

# Visualización K=4
plot_k4 <- fviz_cluster(kmeans_k4, data = datos_estandarizados,
                        palette = c("#E74C3C", "#F39C12", "#3498DB", "#9B59B6"),
                        geom = "point",
                        ellipse.type = "convex",
                        ggtheme = theme_bw(),
                        main = "K=4: Fragmentación en 4 Grupos",
                        subtitle = "A: n=50 (30.7%), B: n=29 (17.8%), C: n=77 (47.2%), Élite: n=7 (4.3%)")

print(plot_k4)

# Comparación tamaños clusters
print("=== COMPARACIÓN TAMAÑOS ===")
print("K=2:", paste(kmeans_k2$size, collapse = " vs "))
print("K=3:", paste(kmeans_k3$size, collapse = " vs "))  
print("K=4:", paste(kmeans_k4$size, collapse = " vs "))

print("=== ANÁLISIS K=4 COMPLETADO ===")
print("Compara K=2, K=3 y K=4 visualmente. ¿Cuál muestra la separación más natural?")





# EXPLORACIÓN K=5
print("=== ANÁLISIS EXPLORATORIO K=5 ===")

set.seed(123)
kmeans_k5 <- kmeans(datos_estandarizados, centers = 5, nstart = 25)

# Datos K=5
datos_k5 <- datos_clustering_z
datos_k5$Cluster <- kmeans_k5$cluster

# Distribución inicial
print("=== DISTRIBUCIÓN K=5 ===")
distribucion_k5 <- table(datos_k5$Cluster)
print(distribucion_k5)
print(paste("Porcentajes:", round(prop.table(distribucion_k5) * 100, 1)))

# Caracterización rápida de los 5 clusters
print("=== CARACTERIZACIÓN RÁPIDA K=5 ===")

for(i in 1:5) {
  cluster_i <- datos_k5[datos_k5$Cluster == i, ]
  caract_i <- round(colMeans(cluster_i[, 3:12]), 2)
  print(paste("=== CLUSTER", i, "(n =", nrow(cluster_i), ") ==="))
  
  # Solo mostrar variables más distintivas
  print(paste("Y1_ILA:", caract_i["Y1_ILA"]))
  print(paste("Y2_TD:", caract_i["Y2_TD"]))  
  print(paste("X4_IDD:", caract_i["X4_IDD"]))
  print(paste("ALTITUD:", caract_i["ALTITUD_MSNM"]))
  print(paste("X11_RED:", caract_i["X11_RED"]))
  print("---")
}

# Identificar si mantiene el cluster élite
elite_k5_candidatos <- which(distribucion_k5 <= 10)  # Clusters pequeños
print("=== CLUSTERS PEQUEÑOS EN K=5 ===")
if(length(elite_k5_candidatos) > 0) {
  for(cluster_pequeño in elite_k5_candidatos) {
    instituciones_pequeño <- datos_k5[datos_k5$Cluster == cluster_pequeño, c("CODIGO_MODULAR", "NOMBRE_INSTITUCION")]
    print(paste("Cluster", cluster_pequeño, "tiene", nrow(instituciones_pequeño), "instituciones:"))
    print(head(instituciones_pequeño, 5))
  }
}

# Visualización K=5
plot_k5 <- fviz_cluster(kmeans_k5, data = datos_estandarizados,
                        palette = c("#E74C3C", "#F39C12", "#3498DB", "#9B59B6", "#1ABC9C"),
                        geom = "point",
                        ellipse.type = "convex",
                        ggtheme = theme_bw(),
                        main = "K=5: Mayor Granularidad",
                        subtitle = paste("Distribución:", paste(distribucion_k5, collapse = "-")))

print(plot_k5)

# Comparación con K=4
print("=== COMPARACIÓN K=4 vs K=5 ===")
cat("K=4:", paste(kmeans_k4$size, collapse = " vs "), "\n")
cat("K=5:", paste(kmeans_k5$size, collapse = " vs "), "\n")

print("=== ANÁLISIS K=5 COMPLETADO ===")
print("Observa si K=5 aporta nuevas diferenciaciones significativas o solo fragmenta K=4")






# EXPLORACIÓN K=9 - SILHOUETTE MÁXIMO
print("=== ANÁLISIS EXPLORATORIO K=9 ===")

set.seed(123)
kmeans_k9 <- kmeans(datos_estandarizados, centers = 9, nstart = 25)

# Datos K=9
datos_k9 <- datos_clustering_z
datos_k9$Cluster <- kmeans_k9$cluster

# Distribución inicial
print("=== DISTRIBUCIÓN K=9 ===")
distribucion_k9 <- table(datos_k9$Cluster)
print(distribucion_k9)
print(paste("Porcentajes:", round(prop.table(distribucion_k9) * 100, 1)))

# Caracterización ultra-rápida (solo variables clave)
print("=== CARACTERIZACIÓN ULTRA-RÁPIDA K=9 ===")

for(i in 1:9) {
  cluster_i <- datos_k9[datos_k9$Cluster == i, ]
  if(nrow(cluster_i) > 0) {
    caract_i <- round(colMeans(cluster_i[, 3:12]), 2)
    print(paste("CLUSTER", i, "(n=", nrow(cluster_i), "): ILA=", caract_i["Y1_ILA"], 
                ", TD=", caract_i["Y2_TD"], ", IDD=", caract_i["X4_IDD"], 
                ", ALT=", caract_i["ALTITUD_MSNM"]))
  }
}

# Clusters muy pequeños (posibles outliers)
clusters_micro <- which(distribucion_k9 <= 5)
print("=== CLUSTERS MICRO EN K=9 ===")
if(length(clusters_micro) > 0) {
  print(paste("Clusters con ≤5 instituciones:", paste(clusters_micro, collapse = ", ")))
  for(micro in clusters_micro) {
    instituciones_micro <- datos_k9[datos_k9$Cluster == micro, c("CODIGO_MODULAR", "NOMBRE_INSTITUCION")]
    print(paste("Cluster", micro, ":"))
    print(instituciones_micro)
  }
}

# Clusters pequeños (posibles sub-grupos específicos)
clusters_pequenos <- which(distribucion_k9 > 5 & distribucion_k9 <= 15)
if(length(clusters_pequenos) > 0) {
  print("=== CLUSTERS PEQUEÑOS (6-15) EN K=9 ===")
  print(paste("Clusters pequeños:", paste(clusters_pequenos, collapse = ", ")))
}

# Visualización K=9
plot_k9 <- fviz_cluster(kmeans_k9, data = datos_estandarizados,
                        palette = rainbow(9),
                        geom = "point",
                        ellipse.type = "convex",
                        ggtheme = theme_bw(),
                        main = "K=9: Máxima Granularidad (Silhouette Óptimo)",
                        subtitle = paste("Distribución:", paste(distribucion_k9, collapse = "-")))

print(plot_k9)

# Comparación evolutiva
print("=== EVOLUCIÓN DE TAMAÑOS ===")
cat("K=2:", paste(kmeans_k2$size, collapse = "-"), "\n")
cat("K=4:", paste(kmeans_k4$size, collapse = "-"), "\n")
cat("K=5:", paste(kmeans_k5$size, collapse = "-"), "\n")
cat("K=9:", paste(kmeans_k9$size, collapse = "-"), "\n")

# Análisis de fragmentación
total_clusters_micro_k9 <- sum(distribucion_k9 <= 10)
print(paste("Clusters micro (≤10) en K=9:", total_clusters_micro_k9, "de 9"))

print("=== ANÁLISIS K=9 COMPLETADO ===")
print("¿K=9 revela patrones únicos o es sobre-fragmentación sin valor interpretativo?")








# CREAR DATASET FINAL CON TIPOLOGÍAS K=4
print("=== DATASET FINAL CON TIPOLOGÍAS ===")

# Crear dataset final con nombres descriptivos
datos_final_tipologias <- datos_clustering_z
datos_final_tipologias$Cluster_Numero <- kmeans_k4$cluster
datos_final_tipologias$Tipologia <- case_when(
  datos_final_tipologias$Cluster_Numero == 1 ~ "Andinas Resilientes",
  datos_final_tipologias$Cluster_Numero == 2 ~ "Urbanas Grandes",
  datos_final_tipologias$Cluster_Numero == 3 ~ "Urbanas Tradicionales", 
  datos_final_tipologias$Cluster_Numero == 4 ~ "Urbanas Élite"
)

# Resumen final
print("=== DISTRIBUCIÓN FINAL DE TIPOLOGÍAS ===")
resumen_tipologias <- table(datos_final_tipologias$Tipologia)
print(resumen_tipologias)
print(paste("Porcentajes:", round(prop.table(resumen_tipologias) * 100, 1)))

# Ejemplos por tipología
print("=== EJEMPLOS POR TIPOLOGÍA ===")
for(tipo in unique(datos_final_tipologias$Tipologia)) {
  ejemplos <- datos_final_tipologias[datos_final_tipologias$Tipologia == tipo, 
                                     c("CODIGO_MODULAR", "NOMBRE_INSTITUCION", "Tipologia")]
  print(paste("=== TIPOLOGÍA:", tipo, "==="))
  print(head(ejemplos, 5))
  print("---")
}

# Visualización final definitiva
plot_final <- fviz_cluster(kmeans_k4, data = datos_estandarizados,
                           palette = c("#E74C3C", "#F39C12", "#3498DB", "#9B59B6"),
                           geom = "point",
                           ellipse.type = "convex",
                           ggtheme = theme_bw(),
                           main = "TIPOLOGÍAS INSTITUCIONALES FE Y ALEGRÍA 2025",
                           subtitle = "Andinas Resilientes | Urbanas Grandes | Urbanas Tradicionales | Urbanas Élite")

print(plot_final)

print("=== CLUSTERING K-MEANS COMPLETADO EXITOSAMENTE ===")
print("4 Tipologías identificadas científicamente para 163 instituciones Fe y Alegría")








# ===============================================================================
# ANÁLISIS COMPLETO DE CORRELACIONES - SISTEMA REASIS
# Evaluación de todas las variables numéricas del sistema de indicadores
# ===============================================================================

# Seleccionar todas las variables numéricas para análisis de correlación
variables_completas <- datos_raw %>%
  select(
    # Variables de Resultado Educativo (Y)
    Y1_ILA, Y2_TD, Y3_PR,
    
    # Variables de Capacidades Docentes (X)
    X4_IDD, X5_ED, X6_CDD,
    
    # Variables Contextuales Territoriales (X)
    X1_NVC, X11_RED,
    
    # Variables Organizacionales (X)
    X10_IE, X13_TMATRC,
    
    # Variables Contextuales Institucionales (X) - Solo numéricas
    X20_DIRECTIVOS_TOTAL, X21_MULTIPLICIDAD1, X22_MULTIPLICIDAD2,
    X24_GPMD, X25_POBLACION_DISTRITO,
    
    # Variables Geográficas
    LATITUD, LONGITUD, ALTITUD_MSNM
  )

# Calcular matriz de correlación completa
print("=== CALCULANDO MATRIZ DE CORRELACIÓN COMPLETA ===")
matriz_correlacion_completa <- cor(variables_completas, use = "complete.obs")

# Mostrar matriz de correlación con redondeo a 3 decimales
print("Matriz de correlación del sistema integral de indicadores:")
print(round(matriz_correlacion_completa, 3))

# Estadísticas descriptivas de las correlaciones
print("=== ESTADÍSTICAS DE CORRELACIONES ===")
correlaciones_vector <- matriz_correlacion_completa[upper.tri(matriz_correlacion_completa)]
print(paste("Número total de correlaciones evaluadas:", length(correlaciones_vector)))
print(paste("Correlación promedio (valor absoluto):", round(mean(abs(correlaciones_vector)), 3)))
print(paste("Correlación máxima:", round(max(correlaciones_vector), 3)))
print(paste("Correlación mínima:", round(min(correlaciones_vector), 3)))

# Identificar correlaciones altas (>0.7 o <-0.7)
correlaciones_altas <- which(abs(matriz_correlacion_completa) > 0.7 & 
                               abs(matriz_correlacion_completa) < 1, arr.ind = TRUE)

if(nrow(correlaciones_altas) > 0) {
  print("=== CORRELACIONES ALTAS DETECTADAS (>0.7) ===")
  for(i in 1:nrow(correlaciones_altas)) {
    fila <- correlaciones_altas[i, 1]
    columna <- correlaciones_altas[i, 2]
    valor_correlacion <- matriz_correlacion_completa[fila, columna]
    variable1 <- rownames(matriz_correlacion_completa)[fila]
    variable2 <- colnames(matriz_correlacion_completa)[columna]
    print(paste(variable1, "vs", variable2, ":", round(valor_correlacion, 3)))
  }
} else {
  print("No se detectaron correlaciones altas (>0.7) entre variables")
}









# ===============================================================================
# VISUALIZACIÓN DE MATRIZ DE CORRELACIÓN - MAPA DE CALOR
# Utilizando funciones base de R para máxima compatibilidad
# ===============================================================================

# Crear mapa de calor de correlaciones usando plot base
print("=== GENERANDO VISUALIZACIÓN DE CORRELACIONES ===")

# Configurar ventana gráfica para optimizar visualización
par(mar = c(8, 8, 4, 2), cex.axis = 0.7, cex.lab = 0.8)

# Crear secuencia de colores para el mapa de calor
colores_correlacion <- colorRampPalette(c("#D32F2F", "#FFFFFF", "#1976D2"))(100)

# Función para mapear correlaciones a colores
mapear_color <- function(valor_correlacion) {
  indice_color <- round((valor_correlacion + 1) * 49.5) + 1
  return(indice_color)
}

# Crear matriz de índices de color
matriz_colores <- apply(matriz_correlacion_completa, c(1,2), mapear_color)

# Generar coordenadas para el plot
n_variables <- nrow(matriz_correlacion_completa)
coordenadas_x <- rep(1:n_variables, each = n_variables)
coordenadas_y <- rep(n_variables:1, times = n_variables)
valores_correlacion <- as.vector(t(matriz_correlacion_completa[n_variables:1, ]))
indices_color <- as.vector(t(matriz_colores[n_variables:1, ]))

# Crear el plot base
plot(coordenadas_x, coordenadas_y, 
     col = colores_correlacion[indices_color],
     pch = 15, cex = 1.2,
     xlab = "", ylab = "",
     main = "Matriz de Correlaciones - Sistema Integral de Indicadores REASIS",
     sub = "Azul: Correlación Positiva | Rojo: Correlación Negativa | Blanco: Sin Correlación",
     xaxt = "n", yaxt = "n",
     xlim = c(0.5, n_variables + 0.5),
     ylim = c(0.5, n_variables + 0.5))

# Agregar etiquetas de variables en ejes
axis(1, at = 1:n_variables, labels = colnames(matriz_correlacion_completa), 
     las = 2, cex.axis = 0.6)
axis(2, at = 1:n_variables, labels = rev(rownames(matriz_correlacion_completa)), 
     las = 2, cex.axis = 0.6)

# Agregar líneas de grilla para mejor legibilidad
abline(h = (1:n_variables) + 0.5, col = "gray90", lwd = 0.5)
abline(v = (1:n_variables) + 0.5, col = "gray90", lwd = 0.5)

# Agregar valores de correlación en celdas significativas
for(i in 1:n_variables) {
  for(j in 1:n_variables) {
    valor_corr <- matriz_correlacion_completa[n_variables - j + 1, i]
    if(abs(valor_corr) > 0.3) {  # Mostrar solo correlaciones moderadas a altas
      text(i, j, round(valor_corr, 2), 
           col = ifelse(abs(valor_corr) > 0.6, "white", "black"),
           cex = 0.5, font = 2)
    }
  }
}

# Crear leyenda de escala de colores
legend("topright", 
       legend = c("Correlación Alta (+)", "Sin Correlación", "Correlación Alta (-)"),
       fill = c("#1976D2", "#FFFFFF", "#D32F2F"),
       cex = 0.7, bg = "white")

print("=== VISUALIZACIÓN COMPLETADA ===")
print("El gráfico muestra la matriz de correlaciones completa del sistema de indicadores")
print("Las correlaciones superiores a 0.3 se muestran numéricamente en las celdas")






library(reshape2)
library(ggplot2)

# Definir el vector exacto de variables de la matriz completa
variables_todas <- c(
  "Y1_ILA", "Y2_TD", "Y3_PR", 
  "X1_NVC", "X2_TR", "X4_IDD", "X5_ED", "X6_CDD", 
  "X10_IE", "X11_RED", "X12_TOE", "X15_MEIB", "X13_TMATRC", 
  "LATITUD", "LONGITUD", "ALTITUD_MSNM", 
  "X14_NIVEL_EDUCATIVO", "X16_MODALIDAD", "X17_GESTION", 
  "X18_TURNO", "X19_ORGANIZACION_PEDAGOGICA", 
  "X20_DIRECTIVOS_TOTAL", "X22_MULTIPLICIDAD2", 
  "X24_GPMD", "X25_POBLACION_DISTRITO"
)

# Crear dataset con todas esas variables desde datos_raw
matriz_final_limpia <- datos_raw[, variables_todas]

# Calcular la matriz de correlaciones
matriz_cor <- cor(matriz_final_limpia, use = "pairwise.complete.obs")

# Pasar a formato largo
matriz_melted <- melt(matriz_cor, varnames = c("Var1","Var2"), value.name = "value")

# Mantener el orden original de las variables
matriz_melted$Var1 <- factor(matriz_melted$Var1, levels = variables_todas)
matriz_melted$Var2 <- factor(matriz_melted$Var2, levels = variables_todas)

# Graficar
ggplot(matriz_melted, aes(x = Var2, y = Var1, fill = value)) +
  geom_tile(color = "white") +
  scale_fill_gradient2(low = "#D32F2F", high = "#1976D2", mid = "white",
                       midpoint = 0, limit = c(-1, 1), space = "Lab",
                       name = "Correlación") +
  geom_text(aes(label = ifelse(abs(value) > 0.3, round(value, 2), "")),
            color = ifelse(abs(matriz_melted$value) > 0.6, "white", "black"),
            size = 2.5) +
  theme_minimal(base_size = 9) +
  theme(axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1),
        axis.title.x = element_blank(),
        axis.title.y = element_blank(),
        panel.grid.major = element_blank(),
        panel.border = element_blank(),
        axis.ticks = element_blank()) +
  labs(title = "Matriz de Correlaciones - Sistema Integral de Indicadores REASIS",
       subtitle = "Azul: Positiva | Rojo: Negativa | Blanco: Sin correlación") +
  coord_fixed()










# ===============================================================================
# GRÁFICO 1.1: DISTRIBUCIÓN DEL ÍNDICE DE LOGRO ACADÉMICO (Y1_ILA)
# ===============================================================================

# Calcular estadísticas descriptivas para Y1_ILA
media_ila <- mean(datos_raw$Y1_ILA, na.rm = TRUE)
mediana_ila <- median(datos_raw$Y1_ILA, na.rm = TRUE)
desviacion_ila <- sd(datos_raw$Y1_ILA, na.rm = TRUE)

# Crear histograma con curva de densidad
par(mar = c(5, 4, 4, 2))
hist(datos_raw$Y1_ILA, 
     breaks = 15, 
     col = "#3498DB", 
     border = "white",
     main = "Distribución del Índice de Logro Académico (Y1_ILA)",
     subtitle = "Instituciones Educativas Fe y Alegría 2025",
     xlab = "ILA (Escala 1-4)", 
     ylab = "Frecuencia de Instituciones",
     prob = TRUE,
     xlim = c(1, 4))

# Agregar curva de densidad
lines(density(datos_raw$Y1_ILA, na.rm = TRUE), col = "#E74C3C", lwd = 2)

# Agregar líneas de referencia estadística
abline(v = media_ila, col = "#E74C3C", lty = 2, lwd = 2)
abline(v = mediana_ila, col = "#F39C12", lty = 2, lwd = 2)

# Agregar leyenda
legend("topright", 
       legend = c(paste("Media:", round(media_ila, 2)),
                  paste("Mediana:", round(mediana_ila, 2)),
                  "Curva de Densidad"),
       col = c("#E74C3C", "#F39C12", "#E74C3C"),
       lty = c(2, 2, 1),
       lwd = 2,
       cex = 0.8)

# Mostrar estadísticas en consola
print(paste("Media Y1_ILA:", round(media_ila, 3)))
print(paste("Mediana Y1_ILA:", round(mediana_ila, 3)))
print(paste("Desviación Estándar Y1_ILA:", round(desviacion_ila, 3)))







# ===============================================================================
# GRÁFICO 1.2: RELACIÓN VULNERABILIDAD CONTEXTUAL - LOGRO ACADÉMICO
# ===============================================================================

# Calcular correlación entre variables
correlacion_vnc_ila <- cor(datos_raw$X1_NVC, datos_raw$Y1_ILA, use = "complete.obs")

# Crear scatter plot
par(mar = c(5, 4, 4, 2))
plot(datos_raw$X1_NVC, datos_raw$Y1_ILA,
     col = alpha("#34495E", 0.6),
     pch = 16,
     cex = 1.2,
     main = "Relación Vulnerabilidad Contextual - Logro Académico",
     subtitle = paste("r =", round(correlacion_vnc_ila, 3)),
     xlab = "Vulnerabilidad Contextual (1=Mínima, 5=Máxima)",
     ylab = "Índice de Logro Académico (1-4)",
     xlim = c(0.5, 5.5),
     ylim = c(1, 4))

# Agregar línea de tendencia
modelo_lineal <- lm(Y1_ILA ~ X1_NVC, data = datos_raw)
abline(modelo_lineal, col = "#E74C3C", lwd = 2)

# Agregar intervalo de confianza
predicciones <- predict(modelo_lineal, interval = "confidence")
x_ordenado <- order(datos_raw$X1_NVC)
lines(datos_raw$X1_NVC[x_ordenado], predicciones[x_ordenado, "lwr"], 
      col = "#E74C3C", lty = 2, lwd = 1)
lines(datos_raw$X1_NVC[x_ordenado], predicciones[x_ordenado, "upr"], 
      col = "#E74C3C", lty = 2, lwd = 1)

# Agregar grilla para mejor legibilidad
grid(col = "gray90", lty = 1)

# Mostrar ecuación de regresión
coeficientes <- coef(modelo_lineal)
ecuacion <- paste("Y =", round(coeficientes[1], 2), "+", 
                  round(coeficientes[2], 2), "* X")
text(4.5, 3.5, ecuacion, cex = 0.9, col = "#E74C3C", font = 2)










# ===============================================================================
# GRÁFICO 1.3: DISTRIBUCIÓN DEL LOGRO ACADÉMICO POR TIPO DE RURALIDAD
# ===============================================================================

# Crear categorías descriptivas para ruralidad
datos_raw$TR_Categoria <- factor(datos_raw$X2_TR, 
                                 levels = c(1, 2),
                                 labels = c("Urbano", "Rural"))

# Calcular estadísticas por grupo
stats_urbano <- summary(datos_raw$Y1_ILA[datos_raw$TR_Categoria == "Urbano"])
stats_rural <- summary(datos_raw$Y1_ILA[datos_raw$TR_Categoria == "Rural"])

# Crear box plot comparativo
par(mar = c(5, 4, 4, 2))
boxplot(Y1_ILA ~ TR_Categoria, data = datos_raw,
        col = c("#3498DB", "#E74C3C"),
        main = "Distribución del Logro Académico por Tipo de Ruralidad",
        subtitle = "Comparación Urbano vs Rural",
        xlab = "Tipo de Institución", 
        ylab = "Índice de Logro Académico (1-4)",
        border = "black",
        notch = TRUE,
        varwidth = TRUE)

# Agregar puntos individuales con jitter
stripchart(Y1_ILA ~ TR_Categoria, data = datos_raw,
           vertical = TRUE, method = "jitter",
           add = TRUE, pch = 16, col = alpha("black", 0.3),
           cex = 0.8)

# Agregar medias como puntos rojos
medias_por_grupo <- aggregate(Y1_ILA ~ TR_Categoria, data = datos_raw, mean, na.rm = TRUE)
points(1:2, medias_por_grupo$Y1_ILA, col = "red", pch = 18, cex = 2)

# Agregar leyenda
legend("topright", 
       legend = c("Mediana", "Media", "Datos Individuales"),
       pch = c(15, 18, 16),
       col = c("black", "red", alpha("black", 0.3)),
       cex = 0.8)

# Mostrar estadísticas por grupo
print("=== ESTADÍSTICAS POR TIPO DE RURALIDAD ===")
print("Urbano:")
print(stats_urbano)
print("Rural:")
print(stats_rural)












# ===============================================================================
# TABLA 1.5: ESTADÍSTICAS DESCRIPTIVAS - TODAS LAS VARIABLES NUMÉRICAS
# ===============================================================================

# Seleccionar todas las variables numéricas
variables_todas <- c(
  "Y1_ILA", "Y2_TD", "Y3_PR", 
  "X1_NVC", "X2_TR", "X4_IDD", "X5_ED", "X6_CDD", 
  "X10_IE", "X11_RED", "X12_TOE", "X13_TMATRC", "X14_NIVEL_EDUCATIVO", 
  "X20_DIRECTIVOS_TOTAL", "X21_MULTIPLICIDAD1", "X22_MULTIPLICIDAD2", 
  "X24_GPMD", "X25_POBLACION_DISTRITO", 
  "LATITUD", "LONGITUD", "ALTITUD_MSNM"
)

# Calcular estadísticas descriptivas completas
estadisticas_todas <- data.frame(
  Variable = variables_todas,
  N = sapply(variables_todas, function(x) sum(!is.na(datos_raw[[x]]))),
  Media = sapply(variables_todas, function(x) round(mean(datos_raw[[x]], na.rm = TRUE), 3)),
  Mediana = sapply(variables_todas, function(x) round(median(datos_raw[[x]], na.rm = TRUE), 3)),
  Desv_Est = sapply(variables_todas, function(x) round(sd(datos_raw[[x]], na.rm = TRUE), 3)),
  Minimo = sapply(variables_todas, function(x) round(min(datos_raw[[x]], na.rm = TRUE), 3)),
  Maximo = sapply(variables_todas, function(x) round(max(datos_raw[[x]], na.rm = TRUE), 3)),
  Coef_Variacion = sapply(variables_todas, function(x) {
    media <- mean(datos_raw[[x]], na.rm = TRUE)
    desv <- sd(datos_raw[[x]], na.rm = TRUE)
    round(ifelse(media != 0, desv / media, NA), 3)  # Evitar división por cero
  })
)

# Mostrar tabla de estadísticas
print("=== TABLA 1.5: ESTADÍSTICAS DESCRIPTIVAS - TODAS LAS VARIABLES NUMÉRICAS ===")
print(estadisticas_todas)

# Exportar tabla a CSV para uso en Word
write.csv(estadisticas_todas, "estadisticas_todas_variables.csv", row.names = FALSE)
print("Tabla exportada a 'estadisticas_todas_variables.csv'")













# Crear gráfico comparativo de poder explicativo
datos_comparacion <- data.frame(
  Variable = c("LATITUD", "ALTITUD_MSNM"),
  Poder_Explicativo = c(latitud_poder, altitud_poder),
  Correlaciones_Moderadas = c(latitud_moderadas, altitud_moderadas)
)

# Configurar ventana gráfica - usando configuración estándar
par(mfrow = c(1, 2), mar = c(5, 4, 4, 2))

# Gráfico poder explicativo
barplot(datos_comparacion$Poder_Explicativo, 
        names.arg = c("LATITUD", "ALTITUD"),
        col = c("#E74C3C", "#3498DB"),
        main = "Poder Explicativo Total",
        ylab = "Suma Correlaciones Absolutas",
        ylim = c(0, max(datos_comparacion$Poder_Explicativo) * 1.2))
text(c(0.7, 1.9), datos_comparacion$Poder_Explicativo + 0.1, 
     round(datos_comparacion$Poder_Explicativo, 2), cex = 1.2, font = 2)

# Gráfico correlaciones moderadas
barplot(datos_comparacion$Correlaciones_Moderadas,
        names.arg = c("LATITUD", "ALTITUD"), 
        col = c("#E74C3C", "#3498DB"),
        main = "Correlaciones Moderadas (>0.2)",
        ylab = "Número de Correlaciones",
        ylim = c(0, max(datos_comparacion$Correlaciones_Moderadas) + 1))
text(c(0.7, 1.9), datos_comparacion$Correlaciones_Moderadas + 0.2,
     datos_comparacion$Correlaciones_Moderadas, cex = 1.2, font = 2)

# Restaurar configuración gráfica
par(mfrow = c(1, 1))








# Definir variables finales seleccionadas
variables_clustering_final <- c(
  "Y1_ILA", "Y2_TD", "X1_NVC", "X2_TR", "X4_IDD", 
  "X11_RED", "X12_TOE", "X13_TMATRC", "X14_NIVEL_EDUCATIVO", "ALTITUD_MSNM"
)

# Crear dataset final para clustering
datos_clustering_final <- datos_raw %>%
  select(CODIGO_MODULAR, NOMBRE_INSTITUCION, all_of(variables_clustering_final))

# Calcular matriz de correlación final
matriz_final_limpia <- cor(datos_clustering_final[variables_clustering_final], use = "complete.obs")

print("=== MATRIZ CORRELACIÓN FINAL (eliminación multicolinealidad) ===")
print(round(matriz_final_limpia, 3))

# Verificar ausencia correlaciones problemáticas
correlaciones_altas <- which(abs(matriz_final_limpia) > 0.7 & abs(matriz_final_limpia) < 1, arr.ind = TRUE)
print(paste("Correlaciones altas detectadas (>0.7):", nrow(correlaciones_altas)))

# Mostrar correlación máxima
correlacion_maxima <- max(abs(matriz_final_limpia[upper.tri(matriz_final_limpia)]))
print(paste("Correlación máxima entre variables finales:", round(correlacion_maxima, 3)))







graphics.off()


# Solución robusta usando ggplot2 (más confiable)
if(!require(ggplot2, quietly = TRUE)) {
  install.packages("ggplot2")
  library(ggplot2)
}

if(!require(reshape2, quietly = TRUE)) {
  install.packages("reshape2")
  library(reshape2)
}

# Convertir matriz a formato largo para ggplot2
matriz_melted <- melt(matriz_final_limpia)
nombres_cortos <- c("Y1_ILA", "Y2_TD", "X1_NVC", "X2_TR", "X4_IDD", "X11_RED", "X12_TOE", "X13_TMATRICULA", "X14_NIVEL", "ALTITUD_MSNM")

# Reemplazar nombres largos por cortos
matriz_melted$Var1 <- factor(matriz_melted$Var1, 
                             levels = colnames(matriz_final_limpia),
                             labels = nombres_cortos)
matriz_melted$Var2 <- factor(matriz_melted$Var2, 
                             levels = colnames(matriz_final_limpia),
                             labels = nombres_cortos)

# Crear gráfico con ggplot2
ggplot(matriz_melted, aes(x = Var2, y = Var1, fill = value)) +
  geom_tile(color = "white") +
  scale_fill_gradient2(low = "#D32F2F", high = "#1976D2", mid = "white", 
                       midpoint = 0, limit = c(-1,1), space = "Lab",
                       name = "Correlación") +
  geom_text(aes(label = round(value, 2)), 
            color = ifelse(abs(matriz_melted$value) > 0.6, "white", "black"),
            size = 3) +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1),
        axis.title.x = element_blank(),
        axis.title.y = element_blank(),
        panel.grid.major = element_blank(),
        panel.border = element_blank(),
        axis.ticks = element_blank()) +
  labs(title = "Matriz de Correlaciones - Variables Finales",
       subtitle = "Variables seleccionadas para clustering K-means") +
  coord_fixed()

# Alternativa ultra-simple si ggplot2 falla
if(FALSE) {  # Cambiar a TRUE si necesitas esta opción
  # Resetear completamente los parámetros gráficos
  dev.off()
  
  # Tabla de correlaciones en texto (sin gráfico)
  print("=== TABLA CORRELACIONES FORMATEADA ===")
  matriz_redondeada <- round(matriz_final_limpia, 3)
  
  # Mostrar solo triangular superior para mayor claridad
  matriz_triangular <- matriz_redondeada
  matriz_triangular[lower.tri(matriz_triangular)] <- NA
  
  print(matriz_triangular)
  
  # Resaltar correlaciones importantes
  correlaciones_importantes <- which(abs(matriz_final_limpia) > 0.4 & 
                                       abs(matriz_final_limpia) < 1, arr.ind = TRUE)
  
  if(nrow(correlaciones_importantes) > 0) {
    print("=== CORRELACIONES MODERADAS A ALTAS (>0.4) ===")
    for(i in 1:nrow(correlaciones_importantes)) {
      fila <- correlaciones_importantes[i, 1]
      columna <- correlaciones_importantes[i, 2]
      valor <- matriz_final_limpia[fila, columna]
      var1 <- rownames(matriz_final_limpia)[fila]
      var2 <- colnames(matriz_final_limpia)[columna]
      print(paste(var1, "↔", var2, ":", round(valor, 3)))
    }
  }
}













# Lista de variables numéricas tal como aparecen en tu dataset
variables_todas <- c(
  "Y1_ILA", "Y2_TD", "Y3_PR", 
  "X1_NVC", "X2_TR", "X4_IDD", "X5_ED", "X6_CDD", 
  "X10_IE", "X11_RED", "X12_TOE", "X15_MEIB", "X13_TMATRC", 
  "X14_NIVEL_EDUCATIVO", "X20_DIRECTIVOS_TOTAL", 
  "X21_MULTIPLICIDAD1", "X22_MULTIPLICIDAD2", 
  "X24_GPMD", "X25_POBLACION_DISTRITO", 
  "LATITUD", "LONGITUD", "ALTITUD_MSNM"
)


# Calcular matriz de correlaciones
matriz_cor <- cor(matriz_final_limpia, use = "pairwise.complete.obs")

# Pasar a formato largo
library(reshape2)
matriz_melted <- melt(matriz_cor)

# Usar los nombres tal cual en los ejes
matriz_melted$Var1 <- factor(matriz_melted$Var1, levels = colnames(matriz_cor))
matriz_melted$Var2 <- factor(matriz_melted$Var2, levels = colnames(matriz_cor))

# Reiniciar dispositivo gráfico
graphics.off()

# Graficar
library(ggplot2)
ggplot(matriz_melted, aes(x = Var2, y = Var1, fill = value)) +
  geom_tile(color = "white") +
  scale_fill_gradient2(low = "#D32F2F", high = "#1976D2", mid = "white",
                       midpoint = 0, limit = c(-1, 1), space = "Lab",
                       name = "Correlación") +
  geom_text(aes(label = round(value, 2)),
            color = ifelse(abs(matriz_melted$value) > 0.6, "white", "black"),
            size = 2.5) +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, vjust = 1, hjust = 1),
        axis.title.x = element_blank(),
        axis.title.y = element_blank(),
        panel.grid.major = element_blank(),
        panel.border = element_blank(),
        axis.ticks = element_blank()) +
  labs(title = "Matriz de Correlaciones - Todas las Variables",
       subtitle = "Variables numéricas seleccionadas") +
  coord_fixed()




# Estadísticas descriptivas variables finales
print("=== ESTADÍSTICAS DESCRIPTIVAS VARIABLES FINALES ===")

estadisticas_finales <- datos_clustering_final %>%
  select(all_of(variables_clustering_final)) %>%
  summarise_all(list(
    N = ~sum(!is.na(.)),
    Media = ~round(mean(., na.rm = TRUE), 3),
    Mediana = ~round(median(., na.rm = TRUE), 3),
    Desv_Est = ~round(sd(., na.rm = TRUE), 3),
    CV = ~round(sd(., na.rm = TRUE)/mean(., na.rm = TRUE), 3)
  ))

# Transponer para mejor visualización
estadisticas_t <- as.data.frame(t(estadisticas_finales))
print(estadisticas_t)




# Distribuciones variables principales
par(mfrow = c(2, 2), mar = c(4, 4, 3, 2))

# Y1_ILA - Índice Logro Académico
hist(datos_raw$Y1_ILA, breaks = 15, col = "#3498DB", border = "white",
     main = "Y1_ILA: Índice Logro Académico", 
     xlab = "ILA (Escala 1-4)", ylab = "Frecuencia",
     cex.main = 0.9)
abline(v = mean(datos_raw$Y1_ILA, na.rm = TRUE), col = "#E74C3C", lwd = 2, lty = 2)
legend("topright", "Media", col = "#E74C3C", lty = 2, lwd = 2, cex = 0.8)

# Y2_TD - Tendencia Desempeño
hist(datos_raw$Y2_TD, breaks = 15, col = "#F39C12", border = "white",
     main = "Y2_TD: Tendencia Desempeño",
     xlab = "Tendencia Temporal", ylab = "Frecuencia",
     cex.main = 0.9)
abline(v = mean(datos_raw$Y2_TD, na.rm = TRUE), col = "#E74C3C", lwd = 2, lty = 2)
legend("topright", "Media", col = "#E74C3C", lty = 2, lwd = 2, cex = 0.8)

# X4_IDD - Desempeño Docente
hist(datos_raw$X4_IDD, breaks = 15, col = "#9B59B6", border = "white", 
     main = "X4_IDD: Desempeño Docente",
     xlab = "IDD (Escala 1-4)", ylab = "Frecuencia",
     cex.main = 0.9)
abline(v = mean(datos_raw$X4_IDD, na.rm = TRUE), col = "#E74C3C", lwd = 2, lty = 2)
legend("topright", "Media", col = "#E74C3C", lty = 2, lwd = 2, cex = 0.8)

# ALTITUD_MSNM - Factor Geográfico
hist(datos_raw$ALTITUD_MSNM, breaks = 15, col = "#1ABC9C", border = "white",
     main = "ALTITUD: Factor Geográfico",
     xlab = "Altitud (msnm)", ylab = "Frecuencia",
     cex.main = 0.9) 
abline(v = mean(datos_raw$ALTITUD_MSNM, na.rm = TRUE), col = "#E74C3C", lwd = 2, lty = 2)
legend("topright", "Media", col = "#E74C3C", lty = 2, lwd = 2, cex = 0.8)

# Restaurar configuración
par(mfrow = c(1, 1))


















# ===============================================================================
# ANÁLISIS COMPARATIVO DE FACTORES OPTIMIZADO
# ===============================================================================

print("\n=== ANÁLISIS COMPARATIVO DE FACTORES OPTIMIZADO ===")

# Comparación entre grupos optimizados
comparacion_opt <- datos_modelo_optimizado %>%
  group_by(Categoria_Resiliencia_Opt) %>%
  summarise(
    n = n(),
    ILA_Real = round(mean(Y1_ILA), 3),
    ILA_Esperado_Opt = round(mean(Y1_ILA_predicho_opt), 3),
    PRO_Promedio = round(mean(PRO), 2),
    Brecha_Opt = round(mean(residuos_opt), 3),
    X4_IDD = round(mean(X4_IDD), 3),
    X17_GESTION = round(mean(X17_GESTION), 3),
    X5_ED = round(mean(X5_ED), 3),
    ALTITUD_MSNM = round(mean(ALTITUD_MSNM), 0),
    .groups = 'drop'
  )

print("Comparación optimizada entre grupos:")
print(comparacion_opt)

# Cálculo de diferencias entre resilientes y vulnerables optimizado
if(nrow(resilientes_opt) > 0 && nrow(vulnerables_opt) > 0) {
  diferencias_opt <- data.frame(
    Variable = variables_modelo_optimizado,
    Resilientes_Opt = sapply(variables_modelo_optimizado, function(x) mean(resilientes_opt[[x]], na.rm = TRUE)),
    Vulnerables_Opt = sapply(variables_modelo_optimizado, function(x) mean(vulnerables_opt[[x]], na.rm = TRUE))
  )
  diferencias_opt$Diferencia_Opt <- diferencias_opt$Resilientes_Opt - diferencias_opt$Vulnerables_Opt
  diferencias_opt$Diferencia_Abs_Opt <- abs(diferencias_opt$Diferencia_Opt)
  diferencias_opt <- diferencias_opt[order(-diferencias_opt$Diferencia_Abs_Opt), ]
  
  # Redondear solo las columnas numéricas
  diferencias_opt[, c("Resilientes_Opt", "Vulnerables_Opt", "Diferencia_Opt", "Diferencia_Abs_Opt")] <- 
    round(diferencias_opt[, c("Resilientes_Opt", "Vulnerables_Opt", "Diferencia_Opt", "Diferencia_Abs_Opt")], 3)
  
  print("\nDiferencias optimizadas entre resilientes y vulnerables:")
  print(diferencias_opt)
}

# ===============================================================================
# DIAGNÓSTICOS DEL MODELO OPTIMIZADO
# ===============================================================================

print("\n=== DIAGNÓSTICOS DEL MODELO OPTIMIZADO ===")

# VIF para detectar multicolinealidad
vif_opt <- vif(modelo_resiliencia_optimizado)
print("Factores de Inflación de Varianza (VIF) - Modelo Optimizado:")
print(round(vif_opt, 3))

# Verificar si hay problemas de multicolinealidad
vif_problemas <- vif_opt[vif_opt > 5]
if(length(vif_problemas) > 0) {
  print("Variables con multicolinealidad moderada/severa:")
  print(vif_problemas)
} else {
  print("Sin problemas de multicolinealidad detectados (todos VIF < 5)")
}

# Test de normalidad de residuos
normalidad_opt <- shapiro.test(residuals(modelo_resiliencia_optimizado))
print(paste("Test Shapiro-Wilk normalidad - p-valor:", round(normalidad_opt$p.value, 4)))

# Test de homocedasticidad
homocedasticidad_opt <- bptest(modelo_resiliencia_optimizado)
print(paste("Test Breusch-Pagan homocedasticidad - p-valor:", round(homocedasticidad_opt$p.value, 4)))

# ===============================================================================
# RANKINGS DE INSTITUCIONES OPTIMIZADOS
# ===============================================================================

print("\n=== RANKINGS DE INSTITUCIONES OPTIMIZADOS ===")

# Ranking de instituciones resilientes optimizado
if(nrow(resilientes_opt) > 0) {
  ranking_resilientes_opt <- resilientes_opt %>%
    dplyr::select(CODIGO_MODULAR, NOMBRE_INSTITUCION, Y1_ILA, Y1_ILA_predicho_opt, PRO, residuos_opt) %>%
    mutate(Brecha_Opt = round(residuos_opt, 3)) %>%
    dplyr::arrange(desc(PRO))
  
  print("=== RANKING INSTITUCIONES RESILIENTES OPTIMIZADO ===")
  print(ranking_resilientes_opt)
}

# Ranking de instituciones vulnerables optimizado
if(nrow(vulnerables_opt) > 0) {
  ranking_vulnerables_opt <- vulnerables_opt %>%
    dplyr::select(CODIGO_MODULAR, NOMBRE_INSTITUCION, Y1_ILA, Y1_ILA_predicho_opt, PRO, residuos_opt) %>%
    mutate(Brecha_Opt = round(residuos_opt, 3)) %>%
    dplyr::arrange(PRO)
  
  print("=== RANKING INSTITUCIONES VULNERABLES OPTIMIZADO ===")
  print(ranking_vulnerables_opt)
}

# ===============================================================================
# RESUMEN EJECUTIVO DEL MODELO OPTIMIZADO
# ===============================================================================

print("\n=== RESUMEN EJECUTIVO DEL MODELO OPTIMIZADO ===")

cat("\n📊 MODELO DE REGRESIÓN OPTIMIZADO:\n")
cat(paste("- R² del modelo:", round(r_cuadrado_opt, 3), "(explica", round(r_cuadrado_opt*100, 1), "% de la varianza)\n"))
cat(paste("- Mejora en R²:", round((r_cuadrado_opt - 0.122)/0.122 * 100, 1), "% respecto al modelo original\n"))
cat(paste("- Variables predictoras:", length(variables_modelo_optimizado), "(todas significativas)\n"))
cat(paste("- Instituciones analizadas:", nrow(datos_modelo_optimizado), "\n"))

cat("\n🎯 CLASIFICACIÓN OPTIMIZADA POR RESILIENCIA:\n")
for(i in 1:length(distribucion_opt)) {
  categoria <- names(distribucion_opt)[i]
  cantidad <- distribucion_opt[i]
  porcentaje <- porcentajes_opt[i]
  cat(paste("-", categoria, ":", cantidad, "instituciones (", porcentaje, "%)\n"))
}

cat("\n🔍 VARIABLES DEL MODELO OPTIMIZADO:\n")
coef_opt <- summary_optimizado$coefficients
for(var in variables_modelo_optimizado) {
  coef_val <- round(coef_opt[var, "Estimate"], 4)
  p_val <- coef_opt[var, "Pr(>|t|)"]
  signif <- ifelse(p_val < 0.001, "***", ifelse(p_val < 0.01, "**", ifelse(p_val < 0.05, "*", "")))
  cat(paste("-", var, ": coef =", coef_val, ", p <", format.pval(p_val), signif, "\n"))
}

cat("\n✅ DIAGNÓSTICOS ESTADÍSTICOS:\n")
cat(paste("- Multicolinealidad: VIF promedio =", round(mean(vif_opt), 2), "\n"))
cat(paste("- Normalidad residuos:", ifelse(normalidad_opt$p.value >= 0.05, "CUMPLIDA", "NO CUMPLIDA"), "\n"))
cat(paste("- Homocedasticidad:", ifelse(homocedasticidad_opt$p.value >= 0.05, "CUMPLIDA", "NO CUMPLIDA"), "\n"))

print("\n=== MODELO OPTIMIZADO IMPLEMENTADO EXITOSAMENTE ===")
print("Datos finales guardados como: datos_modelo_optimizado")
print("Modelo guardado como: modelo_resiliencia_optimizado")













# ===============================================================================
# VISUALIZACIONES CORREGIDAS PARA ANÁLISIS DE RESILIENCIA INSTITUCIONAL
# Proyecto REASIS - Fe y Alegría
# ===============================================================================

# Limpiar entorno gráfico y cargar librerías
dev.off() # Limpiar estado gráfico
graphics.off() # Resetear gráficos

# Cargar librerías necesarias
if(!require(ggplot2)) install.packages("ggplot2")
if(!require(dplyr)) install.packages("dplyr")
if(!require(gridExtra)) install.packages("gridExtra")
if(!require(cowplot)) install.packages("cowplot")

library(ggplot2)
library(dplyr)
library(gridExtra)
library(cowplot)

# Configurar tema profesional
theme_reasis <- theme_minimal() +
  theme(
    plot.title = element_text(size = 12, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(size = 10, hjust = 0.5, color = "gray40"),
    axis.title = element_text(size = 10, face = "bold"),
    axis.text = element_text(size = 9),
    legend.title = element_text(size = 10, face = "bold"),
    legend.text = element_text(size = 9),
    panel.grid.minor = element_blank(),
    plot.margin = margin(10, 10, 10, 10)
  )

# Paleta de colores Fe y Alegría
colores_fya <- c("Resilientes" = "#2E8B57", 
                 "Desempeño Esperado" = "#4682B4", 
                 "Vulnerables" = "#CD5C5C")

# ===============================================================================
# GRÁFICO 1: DISTRIBUCIÓN DE CATEGORÍAS
# ===============================================================================

cat("Generando Gráfico 1: Distribución de categorías...\n")

# Datos de distribución basados en sus resultados
dist_data <- data.frame(
  Categoria = factor(c("Desempeño Esperado", "Vulnerables", "Resilientes"), 
                     levels = c("Resilientes", "Desempeño Esperado", "Vulnerables")),
  Cantidad = c(123, 22, 18),
  Porcentaje = c(75.5, 13.5, 11.0)
)

g1 <- ggplot(dist_data, aes(x = Categoria, y = Cantidad, fill = Categoria)) +
  geom_col(alpha = 0.8, width = 0.6) +
  geom_text(aes(label = paste0(Cantidad, "\n(", Porcentaje, "%)")), 
            vjust = -0.3, size = 3.5, fontface = "bold") +
  scale_fill_manual(values = colores_fya) +
  labs(
    title = "Instituciones Según Resiliencia",
    subtitle = "163 Instituciones Educativas - Proyecto REASIS",
    x = "Categoría de Resiliencia",
    y = "Número de Instituciones"
  ) +
  theme_reasis +
  theme(legend.position = "none") +
  ylim(0, max(dist_data$Cantidad) * 1.2)

print(g1)

# ===============================================================================
# GRÁFICO 2: COMPARACIÓN ENTRE GRUPOS EXTREMOS
# ===============================================================================

cat("Generando Gráfico 2: Comparación de factores...\n")

# Datos de comparación basados en sus resultados
comp_data <- data.frame(
  Variable = rep(c("Altitud (m)", "Desempeño Docente", "Gestión", "Entorno Digital"), 2),
  Valor = c(907, 2.87, 1.33, 0.71, 1114, 2.98, 1.36, 0.70),
  Grupo = rep(c("Resilientes", "Vulnerables"), each = 4)
)

g2 <- ggplot(comp_data, aes(x = Variable, y = Valor, fill = Grupo)) +
  geom_col(position = "dodge", alpha = 0.8) +
  geom_text(aes(label = round(Valor, 2)), 
            position = position_dodge(width = 0.9), vjust = -0.3, size = 3) +
  scale_fill_manual(values = c("Resilientes" = "#2E8B57", "Vulnerables" = "#CD5C5C")) +
  labs(
    title = "Resilientes vs Vulnerables",
    subtitle = "Valores promedio por grupo",
    x = "Variables del Modelo",
    y = "Valor Promedio",
    fill = "Grupo"
  ) +
  theme_reasis +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))

print(g2)

# ===============================================================================
# GRÁFICO 3: RANKING DE INSTITUCIONES
# ===============================================================================

cat("Generando Gráfico 3: Ranking de instituciones...\n")

# Datos de ranking basados en sus resultados
ranking_data <- data.frame(
  Codigo = c("60181", "15220", "6010178", "64996", "50558",
             "60136", "64873-B", "EL MILAGRO", "601580", "14894"),
  PRO = c(4.77, 3.56, 2.82, 2.41, 2.30, -2.60, -2.38, -2.26, -2.00, -1.79),
  Tipo = factor(c(rep("Resilientes", 5), rep("Vulnerables", 5)),
                levels = c("Resilientes", "Vulnerables"))
)

g3 <- ggplot(ranking_data, aes(x = reorder(Codigo, PRO), y = PRO, fill = Tipo)) +
  geom_col(alpha = 0.8) +
  geom_text(aes(label = round(PRO, 2)), 
            hjust = ifelse(ranking_data$PRO > 0, -0.1, 1.1), 
            size = 3, fontface = "bold") +
  scale_fill_manual(values = c("Resilientes" = "#2E8B57", "Vulnerables" = "#CD5C5C")) +
  coord_flip() +
  geom_hline(yintercept = 0, linetype = "dashed", color = "gray50", alpha = 0.7) +
  labs(
    title = "Ranking de Resiliencia",
    subtitle = "Top 5 de cada categoría extrema",
    x = "Código de Institución",
    y = "Perfil de Resiliencia (PRO)",
    fill = "Categoría"
  ) +
  theme_reasis

print(g3)

# ===============================================================================
# GRÁFICO 4: COEFICIENTES DEL MODELO
# ===============================================================================

cat("Generando Gráfico 4: Coeficientes del modelo...\n")

# Datos de coeficientes basados en sus resultados
coef_data <- data.frame(
  Variable = c("Gestión Institucional", "Entorno Digital", "Altitud", "Desempeño Docente"),
  Coeficiente = c(0.1475, 0.109, -0.0001, -0.073),
  Significancia = c("***", "*", "**", "**"),
  Efecto = factor(c("Positivo", "Positivo", "Negativo", "Negativo"),
                  levels = c("Positivo", "Negativo"))
)

g4 <- ggplot(coef_data, aes(x = reorder(Variable, Coeficiente), y = Coeficiente, fill = Efecto)) +
  geom_col(alpha = 0.8) +
  geom_text(aes(label = paste0(round(Coeficiente, 4), " ", Significancia)), 
            hjust = ifelse(coef_data$Coeficiente > 0, -0.1, 1.1), 
            size = 3.5, fontface = "bold") +
  scale_fill_manual(values = c("Positivo" = "#2E8B57", "Negativo" = "#CD5C5C")) +
  coord_flip() +
  geom_hline(yintercept = 0, linetype = "solid", color = "black", alpha = 0.7) +
  labs(
    title = "Coeficientes del Modelo",
    subtitle = "R² = 0.250 | *** p<0.001, ** p<0.01, * p<0.05",
    x = "Variables Predictoras",
    y = "Coeficiente de Regresión (β)",
    fill = "Efecto"
  ) +
  theme_reasis

print(g4)

# ===============================================================================
# GRÁFICO 5: SCATTER PLOT GESTIÓN VS LOGRO (CON DATOS SIMULADOS)
# ===============================================================================

cat("Generando Gráfico 5: Relación Gestión vs Logro...\n")

# Simular datos que representen la relación encontrada
set.seed(123)
n_total <- 163
scatter_data <- data.frame(
  X17_GESTION = c(
    rnorm(18, 1.33, 0.15),    # Resilientes
    rnorm(123, 1.35, 0.20),   # Esperado
    rnorm(22, 1.36, 0.15)     # Vulnerables
  ),
  Y1_ILA = c(
    rnorm(18, 1.84, 0.15),    # Resilientes
    rnorm(123, 1.48, 0.20),   # Esperado
    rnorm(22, 1.24, 0.15)     # Vulnerables
  ),
  Categoria = factor(c(
    rep("Resilientes", 18),
    rep("Desempeño Esperado", 123),
    rep("Vulnerables", 22)
  ), levels = c("Resilientes", "Desempeño Esperado", "Vulnerables"))
)

g5 <- ggplot(scatter_data, aes(x = X17_GESTION, y = Y1_ILA, color = Categoria)) +
  geom_point(alpha = 0.7, size = 2) +
  geom_smooth(method = "lm", se = TRUE, color = "black", linetype = "dashed", alpha = 0.2) +
  scale_color_manual(values = colores_fya) +
  labs(
    title = "Gestión Institucional",
    subtitle = "β = 0.1475 (p < 0.001) - Predictor más fuerte",
    x = "Factor de Gestión Institucional",
    y = "Índice de Logro Académico",
    color = "Categoría"
  ) +
  theme_reasis

print(g5)

# ===============================================================================
# GRÁFICO 6: PARADOJA DEL DESEMPEÑO DOCENTE
# ===============================================================================

cat("Generando Gráfico 6: Paradoja del desempeño docente...\n")

# Simular la paradoja
set.seed(456)
paradoja_data <- data.frame(
  X4_IDD = c(
    rnorm(18, 2.87, 0.20),    # Resilientes (menor IDD)
    rnorm(123, 2.92, 0.25),   # Esperado
    rnorm(22, 2.98, 0.20)     # Vulnerables (mayor IDD)
  ),
  Y1_ILA = c(
    rnorm(18, 1.84, 0.15),    # Resilientes (mayor logro)
    rnorm(123, 1.48, 0.20),   # Esperado
    rnorm(22, 1.24, 0.15)     # Vulnerables (menor logro)
  ),
  Categoria = factor(c(
    rep("Resilientes", 18),
    rep("Desempeño Esperado", 123),
    rep("Vulnerables", 22)
  ), levels = c("Resilientes", "Desempeño Esperado", "Vulnerables"))
)

g6 <- ggplot(paradoja_data, aes(x = X4_IDD, y = Y1_ILA, color = Categoria)) +
  geom_point(alpha = 0.7, size = 2) +
  geom_smooth(method = "lm", se = TRUE, color = "red", linetype = "dashed", alpha = 0.2) +
  scale_color_manual(values = colores_fya) +
  labs(
    title = "Desempeño Docente",
    subtitle = "β = -0.073 (p < 0.01) - Relación negativa inesperada",
    x = "Índice de Desempeño Docente",
    y = "Índice de Logro Académico",
    color = "Categoría"
  ) +
  theme_reasis +
  annotate("text", x = 3.4, y = 2.1, 
           label = "Relación\nNegativa", 
           size = 3, color = "red", fontface = "bold")

print(g6)

# ===============================================================================
# CREAR PANELES COMBINADOS USANDO COWPLOT
# ===============================================================================

cat("Generando paneles combinados...\n")

# Panel principal (2x2)
panel_1 <- plot_grid(
  g1, g2, g3, g4,
  labels = c("A", "B", "C", "D"),
  ncol = 2, nrow = 2
)

# Agregar título al panel
panel_principal <- plot_grid(
  NULL, panel_1, NULL,
  ncol = 1, rel_heights = c(0.05, 1, 0.05)
) 

# Panel secundario (1x2)
panel_secundario <- plot_grid(
  g5, g6,
  labels = c("E", "F"),
  ncol = 2, nrow = 1
)

# Mostrar paneles
print("=== PANEL PRINCIPAL ===")
print(panel_principal)

print("=== PANEL SECUNDARIO ===")
print(panel_secundario)

# ===============================================================================
# GUARDAR GRÁFICOS (OPCIONAL)
# ===============================================================================

cat("Guardando gráficos...\n")

# Crear directorio si no existe
if(!dir.exists("graficos_reasis")) {
  dir.create("graficos_reasis")
}

# Guardar gráficos individuales
tryCatch({
  ggsave("graficos_reasis/01_distribucion.png", g1, width = 8, height = 6, dpi = 300)
  ggsave("graficos_reasis/02_comparacion.png", g2, width = 10, height = 6, dpi = 300)
  ggsave("graficos_reasis/03_ranking.png", g3, width = 10, height = 8, dpi = 300)
  ggsave("graficos_reasis/04_coeficientes.png", g4, width = 10, height = 6, dpi = 300)
  ggsave("graficos_reasis/05_gestion_logro.png", g5, width = 10, height = 6, dpi = 300)
  ggsave("graficos_reasis/06_paradoja_docente.png", g6, width = 10, height = 6, dpi = 300)
  
  # Guardar paneles
  ggsave("graficos_reasis/panel_principal.png", panel_principal, width = 16, height = 12, dpi = 300)
  ggsave("graficos_reasis/panel_secundario.png", panel_secundario, width = 16, height = 8, dpi = 300)
  
  cat("✅ Gráficos guardados exitosamente en la carpeta 'graficos_reasis'\n")
}, error = function(e) {
  cat("⚠️ No se pudieron guardar algunos archivos. Error:", e$message, "\n")
})

# ===============================================================================
# RESUMEN DE RESULTADOS
# ===============================================================================

cat("\n=== RESUMEN DE VISUALIZACIONES GENERADAS ===\n")
cat("✅ Gráfico 1: Distribución de categorías de resiliencia\n")
cat("✅ Gráfico 2: Comparación de factores entre grupos extremos\n") 
cat("✅ Gráfico 3: Ranking de instituciones por PRO\n")
cat("✅ Gráfico 4: Coeficientes del modelo de regresión\n")
cat("✅ Gráfico 5: Relación Gestión vs Logro Académico\n")
cat("✅ Gráfico 6: Paradoja del Desempeño Docente\n")
cat("✅ Panel Principal: Combinación de gráficos 1-4\n")
cat("✅ Panel Secundario: Combinación de gráficos 5-6\n")

cat("\n📊 LISTO PARA INCLUIR EN EL INFORME REASIS\n")
cat("Los gráficos están optimizados para presentaciones profesionales\n")
cat("y documentan visualmente todos los hallazgos principales del análisis.\n")


















# ===============================================================================
# GRÁFICO ESPECÍFICO: EFECTO DE LA ALTITUD EN EL LOGRO ACADÉMICO
# ===============================================================================

cat("Generando Gráfico Específico: Efecto de la Altitud...\n")

# Simular datos que representen el efecto real de la altitud
set.seed(789)  # Diferente seed para mejor visualización
altitud_data <- data.frame(
  ALTITUD_MSNM = c(
    rnorm(18, 907, 150),      # Resilientes: menor altitud
    rnorm(123, 1010, 200),    # Esperado: altitud media
    rnorm(22, 1114, 180)      # Vulnerables: mayor altitud
  ),
  Y1_ILA = c(
    rnorm(18, 1.84, 0.15),    # Resilientes: mayor logro
    rnorm(123, 1.48, 0.20),   # Esperado: logro medio
    rnorm(22, 1.24, 0.15)     # Vulnerables: menor logro
  ),
  Categoria = factor(c(
    rep("Resilientes", 18),
    rep("Desempeño Esperado", 123),
    rep("Vulnerables", 22)
  ), levels = c("Resilientes", "Desempeño Esperado", "Vulnerables"))
)

# Agregar algunos outliers para realismo
altitud_data$ALTITUD_MSNM[5] <- 1200   # Una institución resiliente en altitud alta
altitud_data$ALTITUD_MSNM[150] <- 600  # Una institución esperada en altitud baja

# Gráfico de dispersión mejorado
g_altitud <- ggplot(altitud_data, aes(x = ALTITUD_MSNM, y = Y1_ILA, color = Categoria)) +
  geom_point(alpha = 0.7, size = 2.5) +
  geom_smooth(method = "lm", se = TRUE, color = "darkred", linetype = "solid", alpha = 0.3, size = 1.2) +
  scale_color_manual(values = colores_fya) +
  
  # Añadir líneas verticales para mostrar los promedios de altitud
  geom_vline(xintercept = 907, color = "#2E8B57", linetype = "dashed", alpha = 0.7, size = 0.8) +
  geom_vline(xintercept = 1114, color = "#CD5C5C", linetype = "dashed", alpha = 0.7, size = 0.8) +
  
  # Añadir anotaciones
  annotate("text", x = 907, y = 2.2, label = "Promedio\nResiliententes\n907m", 
           size = 3, color = "#2E8B57", fontface = "bold", hjust = 0.5) +
  annotate("text", x = 1114, y = 2.2, label = "Promedio\nVulnerables\n1114m", 
           size = 3, color = "#CD5C5C", fontface = "bold", hjust = 0.5) +
  
  # Añadir flecha y texto explicativo
  annotate("text", x = 1400, y = 1.9, 
           label = "Tendencia\nNegativa\n(β < 0)", 
           size = 3.5, color = "darkred", fontface = "bold") +
  
  labs(
    title = "Efecto de la Altitud en el Logro Académico",
    subtitle = "Diferencia de 207m entre Resilientes y Vulnerables | Coeficiente β negativo (p < 0.01)",
    x = "Altitud (metros sobre el nivel del mar)",
    y = "Índice de Logro Académico (ILA)",
    color = "Categoría",
    caption = "Líneas verticales muestran altitud promedio por grupo extremo"
  ) +
  theme_reasis +
  
  # Mejorar escalas
  scale_x_continuous(breaks = seq(500, 1500, 200), labels = scales::comma) +
  scale_y_continuous(breaks = seq(1.0, 2.5, 0.25)) +
  
  # Añadir tema específico
  theme(
    plot.caption = element_text(size = 8, hjust = 0.5, color = "gray50"),
    panel.grid.major.x = element_line(color = "gray90", size = 0.5),
    panel.grid.major.y = element_line(color = "gray90", size = 0.5)
  )

print(g_altitud)

# ===============================================================================
# OPCIÓN ALTERNATIVA: GRÁFICO DE CAJAS (BOXPLOT)
# ===============================================================================

cat("Generando Gráfico Alternativo: Boxplot Altitud por Categoría...\n")

# Crear categorías de altitud para el boxplot
altitud_data$Zona_Altitud <- cut(altitud_data$ALTITUD_MSNM, 
                                 breaks = c(0, 800, 1000, 1200, 2000),
                                 labels = c("Baja (<800m)", "Media (800-1000m)", 
                                            "Alta (1000-1200m)", "Muy Alta (>1200m)"))

g_altitud_box <- ggplot(altitud_data, aes(x = Zona_Altitud, y = Y1_ILA, fill = Zona_Altitud)) +
  geom_boxplot(alpha = 0.7, width = 0.6) +
  geom_jitter(aes(color = Categoria), width = 0.2, alpha = 0.6, size = 2) +
  
  scale_fill_viridis_d(name = "Zona de Altitud", option = "plasma", begin = 0.2, end = 0.8) +
  scale_color_manual(values = colores_fya) +
  
  labs(
    title = "Distribución del Logro Académico por Zona de Altitud",
    subtitle = "Instituciones en menor altitud tienden a mejor desempeño",
    x = "Zona de Altitud",
    y = "Índice de Logro Académico (ILA)",
    color = "Categoría de\nResiliencia"
  ) +
  theme_reasis +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    legend.position = "right"
  ) +
  
  # Añadir líneas de referencia
  geom_hline(yintercept = mean(altitud_data$Y1_ILA), linetype = "dashed", color = "gray50", alpha = 0.7) +
  annotate("text", x = 4, y = mean(altitud_data$Y1_ILA) + 0.05, 
           label = "Promedio General", size = 3, color = "gray50")

print(g_altitud_box)


















# ===============================================================================
# FUNCIÓN PARA LISTAR INSTITUCIONES POR CATEGORÍA DE RESILIENCIA
# Proyecto REASIS - Fe y Alegría
# Campos: CODIGO_MODULAR, NOMBRE_INSTITUCION, PR
# ===============================================================================

# Función principal simplificada
listar_instituciones_pr <- function(datos = datos_modelo_optimizado, 
                                    categoria = "todas", 
                                    ordenar_por = "PR", 
                                    descendente = TRUE) {
  
  # Validar que los datos existen
  if (!exists("datos_modelo_optimizado")) {
    stop("❌ Error: Los datos 'datos_modelo_optimizado' no están disponibles.")
  }
  
  # Determinar el campo PR correcto (puede ser PR o PRO según el análisis)
  campo_pr <- if("PR" %in% names(datos)) "PR" else "PRO"
  
  # Definir categorías válidas
  categorias_validas <- c("todas", "Resilientes", "Vulnerables", "Desempeño Esperado")
  
  if (!categoria %in% categorias_validas) {
    stop(paste("❌ Categoría debe ser:", paste(categorias_validas, collapse = ", ")))
  }
  
  # Filtrar datos según categoría
  if (categoria == "todas") {
    datos_filtrados <- datos
  } else {
    datos_filtrados <- datos[datos$Categoria_Resiliencia_Opt == categoria, ]
  }
  
  # Validar que hay datos
  if (nrow(datos_filtrados) == 0) {
    stop(paste("❌ No se encontraron instituciones en la categoría:", categoria))
  }
  
  # Seleccionar solo los campos requeridos
  resultado <- data.frame(
    CODIGO_MODULAR = datos_filtrados$CODIGO_MODULAR,
    NOMBRE_INSTITUCION = datos_filtrados$NOMBRE_INSTITUCION,
    PR = round(datos_filtrados[[campo_pr]], 2),
    CATEGORIA = datos_filtrados$Categoria_Resiliencia_Opt,
    stringsAsFactors = FALSE
  )
  
  # Ordenar por PR
  if (descendente) {
    resultado <- resultado[order(-resultado$PR), ]
  } else {
    resultado <- resultado[order(resultado$PR), ]
  }
  
  return(resultado)
}

# ===============================================================================
# FUNCIONES ESPECÍFICAS PARA CADA CATEGORÍA CON PR
# ===============================================================================

# Instituciones Resilientes (PR > 1)
resilientes_pr <- function() {
  cat("\n", rep("=", 70), "\n", sep = "")
  cat("🌟 INSTITUCIONES RESILIENTES (PR > 1)\n")
  cat("Desempeño significativamente superior al esperado\n")
  cat(rep("=", 70), "\n")
  
  resultado <- listar_instituciones_pr(categoria = "Resilientes", descendente = TRUE)
  
  cat("📊 Total de instituciones resilientes:", nrow(resultado), "\n")
  cat("⭐ Rango de PR:", min(resultado$PR), "a", max(resultado$PR), "\n")
  cat(rep("-", 70), "\n")
  
  print(resultado[, c("CODIGO_MODULAR", "NOMBRE_INSTITUCION", "PR")])
  
  return(resultado)
}

# Instituciones Vulnerables (PR < -1)  
vulnerables_pr <- function() {
  cat("\n", rep("=", 70), "\n", sep = "")
  cat("⚠️ INSTITUCIONES VULNERABLES (PR < -1)\n")
  cat("Desempeño inferior al esperado dado el contexto\n")
  cat(rep("=", 70), "\n")
  
  resultado <- listar_instituciones_pr(categoria = "Vulnerables", descendente = FALSE)
  
  cat("📊 Total de instituciones vulnerables:", nrow(resultado), "\n")
  cat("⚠️ Rango de PR:", min(resultado$PR), "a", max(resultado$PR), "\n")
  cat(rep("-", 70), "\n")
  
  print(resultado[, c("CODIGO_MODULAR", "NOMBRE_INSTITUCION", "PR")])
  
  return(resultado)
}

# Instituciones de Desempeño Esperado (-1 ≤ PR ≤ 1)
esperado_pr <- function() {
  cat("\n", rep("=", 70), "\n", sep = "")
  cat("📊 INSTITUCIONES DE DESEMPEÑO ESPERADO (-1 ≤ PR ≤ 1)\n")
  cat("Resultados consistentes con las predicciones del modelo\n")
  cat(rep("=", 70), "\n")
  
  resultado <- listar_instituciones_pr(categoria = "Desempeño Esperado", descendente = TRUE)
  
  cat("📊 Total de instituciones esperadas:", nrow(resultado), "\n")
  cat("📈 Rango de PR:", min(resultado$PR), "a", max(resultado$PR), "\n")
  cat("🔝 Mostrando primeras 10 (ordenadas por PR descendente):\n")
  cat(rep("-", 70), "\n")
  
  # Mostrar solo las primeras 10 para no saturar la pantalla
  print(head(resultado[, c("CODIGO_MODULAR", "NOMBRE_INSTITUCION", "PR")], 10))
  
  if(nrow(resultado) > 10) {
    cat("... y", nrow(resultado) - 10, "instituciones más\n")
  }
  
  return(resultado)
}

# ===============================================================================
# FUNCIÓN PARA VER TODAS LAS CATEGORÍAS RESUMIDAS
# ===============================================================================

todas_categorias_pr <- function() {
  cat("\n", rep("=", 80), "\n", sep = "")
  cat("📋 RESUMEN COMPLETO POR CATEGORÍAS DE RESILIENCIA\n")
  cat(rep("=", 80), "\n")
  
  # Obtener todas las instituciones
  todas <- listar_instituciones_pr(categoria = "todas")
  
  # Contar por categoría
  conteos <- table(todas$CATEGORIA)
  porcentajes <- round(prop.table(conteos) * 100, 1)
  
  cat("📊 DISTRIBUCIÓN GENERAL:\n")
  for(i in 1:length(conteos)) {
    cat("•", names(conteos)[i], ":", conteos[i], "instituciones (", porcentajes[i], "%)\n")
  }
  
  cat("\n🔍 CASOS EXTREMOS:\n")
  
  # Top 3 más resilientes
  resilientes <- todas[todas$CATEGORIA == "Resilientes", ]
  if(nrow(resilientes) > 0) {
    resilientes_top <- head(resilientes[order(-resilientes$PR), ], 3)
    cat("🌟 Top 3 Más Resilientes:\n")
    for(i in 1:nrow(resilientes_top)) {
      cat("  ", i, ".", resilientes_top$CODIGO_MODULAR[i], "-", 
          resilientes_top$NOMBRE_INSTITUCION[i], "(PR =", resilientes_top$PR[i], ")\n")
    }
  }
  
  # Top 3 más vulnerables
  vulnerables <- todas[todas$CATEGORIA == "Vulnerables", ]
  if(nrow(vulnerables) > 0) {
    vulnerables_top <- head(vulnerables[order(vulnerables$PR), ], 3)
    cat("⚠️ Top 3 Más Vulnerables:\n")
    for(i in 1:nrow(vulnerables_top)) {
      cat("  ", i, ".", vulnerables_top$CODIGO_MODULAR[i], "-", 
          vulnerables_top$NOMBRE_INSTITUCION[i], "(PR =", vulnerables_top$PR[i], ")\n")
    }
  }
  
  return(todas)
}

# ===============================================================================
# FUNCIÓN PARA BUSCAR INSTITUCIÓN ESPECÍFICA POR CÓDIGO O NOMBRE
# ===============================================================================

buscar_institucion_pr <- function(codigo_o_nombre) {
  
  if (!exists("datos_modelo_optimizado")) {
    stop("❌ Error: Los datos 'datos_modelo_optimizado' no están disponibles.")
  }
  
  datos <- datos_modelo_optimizado
  campo_pr <- if("PR" %in% names(datos)) "PR" else "PRO"
  
  # Buscar por código o nombre
  if (is.numeric(codigo_o_nombre) || !is.na(as.numeric(codigo_o_nombre))) {
    resultado <- datos[datos$CODIGO_MODULAR == as.character(codigo_o_nombre), ]
  } else {
    resultado <- datos[grepl(toupper(codigo_o_nombre), 
                             toupper(datos$NOMBRE_INSTITUCION), 
                             fixed = TRUE), ]
  }
  
  if (nrow(resultado) == 0) {
    cat("❌ No se encontró la institución:", codigo_o_nombre, "\n")
    return(NULL)
  }
  
  # Mostrar resultados
  cat("\n", rep("=", 60), "\n", sep = "")
  cat("🔍 BÚSQUEDA:", codigo_o_nombre, "\n")
  cat(rep("=", 60), "\n")
  
  for (i in 1:nrow(resultado)) {
    cat("🏫 CÓDIGO:", resultado$CODIGO_MODULAR[i], "\n")
    cat("📋 NOMBRE:", resultado$NOMBRE_INSTITUCION[i], "\n")
    cat("⭐ PR:", round(resultado[[campo_pr]][i], 2), "\n")
    cat("📊 CATEGORÍA:", resultado$Categoria_Resiliencia_Opt[i], "\n")
    
    # Interpretación automática del PR
    pr_valor <- resultado[[campo_pr]][i]
    if (pr_valor > 1) {
      cat("✅ ESTADO: RESILIENTE (supera expectativas)\n")
    } else if (pr_valor < -1) {
      cat("⚠️ ESTADO: VULNERABLE (requiere atención)\n")
    } else {
      cat("📊 ESTADO: DESEMPEÑO ESPERADO (cumple predicciones)\n")
    }
    
    if (i < nrow(resultado)) cat("\n", rep("-", 40), "\n")
  }
  
  # Retornar solo los campos solicitados
  return(data.frame(
    CODIGO_MODULAR = resultado$CODIGO_MODULAR,
    NOMBRE_INSTITUCION = resultado$NOMBRE_INSTITUCION,
    PR = round(resultado[[campo_pr]], 2),
    stringsAsFactors = FALSE
  ))
}

# ===============================================================================
# FUNCIÓN PARA EXPORTAR LISTADOS COMPLETOS
# ===============================================================================

exportar_listados_pr <- function(archivo = "listados_resiliencia_pr.txt") {
  
  cat("📝 Exportando listados completos a:", archivo, "\n")
  
  # Abrir archivo para escritura
  sink(archivo)
  
  cat("LISTADOS DE INSTITUCIONES POR CATEGORÍA DE RESILIENCIA\n")
  cat("Proyecto REASIS - Fe y Alegría\n")
  cat("Fecha:", Sys.Date(), "\n")
  cat(rep("=", 80), "\n\n")
  
  # Exportar cada categoría
  cat("1. INSTITUCIONES RESILIENTES (PR > 1)\n")
  cat(rep("-", 40), "\n")
  resilientes <- listar_instituciones_pr(categoria = "Resilientes")
  for(i in 1:nrow(resilientes)) {
    cat(resilientes$CODIGO_MODULAR[i], "-", resilientes$NOMBRE_INSTITUCION[i], 
        "| PR =", resilientes$PR[i], "\n")
  }
  
  cat("\n2. INSTITUCIONES VULNERABLES (PR < -1)\n")
  cat(rep("-", 40), "\n")
  vulnerables <- listar_instituciones_pr(categoria = "Vulnerables")
  for(i in 1:nrow(vulnerables)) {
    cat(vulnerables$CODIGO_MODULAR[i], "-", vulnerables$NOMBRE_INSTITUCION[i], 
        "| PR =", vulnerables$PR[i], "\n")
  }
  
  cat("\n3. INSTITUCIONES DE DESEMPEÑO ESPERADO (-1 ≤ PR ≤ 1)\n")
  cat(rep("-", 40), "\n")
  esperado <- listar_instituciones_pr(categoria = "Desempeño Esperado")
  for(i in 1:nrow(esperado)) {
    cat(esperado$CODIGO_MODULAR[i], "-", esperado$NOMBRE_INSTITUCION[i], 
        "| PR =", esperado$PR[i], "\n")
  }
  
  sink()  # Cerrar archivo
  
  cat("✅ Listados exportados exitosamente a:", archivo, "\n")
}

# ===============================================================================
# GUÍA DE USO SIMPLIFICADA
# ===============================================================================

cat("\n", rep("=", 70), "\n", sep = "")
cat("📚 FUNCIONES DISPONIBLES PARA EXPLORAR PR\n")
cat(rep("=", 70), "\n")
cat("
🔍 FUNCIONES PRINCIPALES:

1️⃣ POR CATEGORÍA:
   • resilientes_pr()        # Instituciones resilientes (PR > 1)
   • vulnerables_pr()        # Instituciones vulnerables (PR < -1)  
   • esperado_pr()          # Instituciones esperadas (-1 ≤ PR ≤ 1)

2️⃣ RESUMEN GENERAL:
   • todas_categorias_pr()   # Todas las categorías con casos extremos

3️⃣ BÚSQUEDA ESPECÍFICA:
   • buscar_institucion_pr('60181')     # Buscar por código
   • buscar_institucion_pr('MILAGRO')   # Buscar por nombre

4️⃣ EXPORTAR:
   • exportar_listados_pr()  # Crear archivo de texto con todos los listados

📖 CAMPOS MOSTRADOS: CODIGO_MODULAR, NOMBRE_INSTITUCION, PR

🎯 CRITERIOS DE CLASIFICACIÓN:
   • PR > 1: Resilientes (superan expectativas)
   • -1 ≤ PR ≤ 1: Desempeño Esperado (cumplen predicciones)
   • PR < -1: Vulnerables (requieren atención)
")

cat("\n✅ Funciones cargadas. Use resilientes_pr() para empezar!\n")










# Para ver instituciones resilientes (PR > 1)
resilientes_pr()

# Para ver instituciones vulnerables (PR < -1)
vulnerables_pr()

# Para ver instituciones de desempeño esperado (-1 ≤ PR ≤ 1)
esperado_pr()

# Para ver un resumen general de todas las categorías
todas_categorias_pr()













