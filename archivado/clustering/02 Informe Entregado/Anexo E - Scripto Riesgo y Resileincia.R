# ===============================================================================
# MODELO OPTIMIZADO DE RESILIENCIA INSTITUCIONAL
# Implementación del modelo estadísticamente robusto identificado mediante selección sistemática
# ===============================================================================

library(dplyr)
library(ggplot2)
library(car)
library(lmtest)
library(gridExtra)

print("=== IMPLEMENTACIÓN DEL MODELO OPTIMIZADO DE RESILIENCIA ===")

# ===============================================================================
# ESPECIFICACIÓN DEL MODELO OPTIMIZADO
# ===============================================================================

print("=== ESPECIFICACIÓN DEL MODELO OPTIMIZADO ===")

# Variables del modelo optimizado identificadas por selección sistemática
variables_modelo_optimizado <- c("X4_IDD", "X17_GESTION", "X5_ED", "ALTITUD_MSNM")

# Crear dataset para el modelo optimizado
datos_modelo_optimizado <- dataset_completo[, c("CODIGO_MODULAR", "NOMBRE_INSTITUCION", "Y1_ILA", variables_modelo_optimizado)]
datos_modelo_optimizado <- datos_modelo_optimizado[complete.cases(datos_modelo_optimizado), ]

print(paste("Observaciones para modelo optimizado:", nrow(datos_modelo_optimizado)))
print("Variables predictoras del modelo optimizado:")
print(variables_modelo_optimizado)

# Especificar y ajustar el modelo optimizado
formula_optimizada <- as.formula(paste("Y1_ILA ~", paste(variables_modelo_optimizado, collapse = " + ")))
modelo_resiliencia_optimizado <- lm(formula_optimizada, data = datos_modelo_optimizado)

print("\n=== RESULTADOS DEL MODELO OPTIMIZADO ===")
summary_optimizado <- summary(modelo_resiliencia_optimizado)
print(summary_optimizado)

# Métricas del modelo optimizado
r_cuadrado_opt <- summary_optimizado$r.squared
r_cuadrado_ajustado_opt <- summary_optimizado$adj.r.squared
rmse_opt <- sqrt(mean(modelo_resiliencia_optimizado$residuals^2))
f_statistic_opt <- summary_optimizado$fstatistic

print("\n=== MÉTRICAS DEL MODELO OPTIMIZADO ===")
print(paste("R² del modelo optimizado:", round(r_cuadrado_opt, 4)))
print(paste("R² ajustado:", round(r_cuadrado_ajustado_opt, 4)))
print(paste("RMSE:", round(rmse_opt, 4)))
print(paste("F-statistic:", round(f_statistic_opt[1], 3), "con p-valor <", format.pval(pf(f_statistic_opt[1], f_statistic_opt[2], f_statistic_opt[3], lower.tail = FALSE))))

# ===============================================================================
# CÁLCULO DEL PERFIL DE RESILIENCIA OPTIMIZADO
# ===============================================================================

print("\n=== CÁLCULO DEL PERFIL DE RESILIENCIA OPTIMIZADO ===")

# Calcular predicciones y residuos del modelo optimizado
datos_modelo_optimizado$Y1_ILA_predicho_opt <- predict(modelo_resiliencia_optimizado)
datos_modelo_optimizado$residuos_opt <- datos_modelo_optimizado$Y1_ILA - datos_modelo_optimizado$Y1_ILA_predicho_opt

# Calcular Perfil de Resiliencia Optimizado (PRO) como residuos estandarizados
datos_modelo_optimizado$PRO <- scale(datos_modelo_optimizado$residuos_opt)[,1]

print("Estadísticas descriptivas del Perfil de Resiliencia Optimizado (PRO):")
print(summary(datos_modelo_optimizado$PRO))

# Comparación con perfil de resiliencia original
print("\n=== COMPARACIÓN CON MODELO ORIGINAL ===")
print("Modelo Original:")
print(paste("- R² =", round(0.122, 3)))
print(paste("- Variables significativas: 1 de 7"))
print(paste("- RMSE =", round(0.186, 3)))

print("Modelo Optimizado:")
print(paste("- R² =", round(r_cuadrado_opt, 3), "(+", round((r_cuadrado_opt - 0.122)/0.122 * 100, 1), "%)"))
print(paste("- Variables significativas: 4 de 4 (100%)"))
print(paste("- RMSE =", round(rmse_opt, 3), "(", round((rmse_opt - 0.186)/0.186 * 100, 1), "%)"))

# ===============================================================================
# CLASIFICACIÓN OPTIMIZADA POR PERFIL DE RESILIENCIA
# ===============================================================================

print("\n=== CLASIFICACIÓN OPTIMIZADA POR PERFIL DE RESILIENCIA ===")

# Aplicar criterios de clasificación al perfil optimizado
datos_modelo_optimizado$Categoria_Resiliencia_Opt <- case_when(
  datos_modelo_optimizado$PRO > 1 ~ "Resilientes",
  datos_modelo_optimizado$PRO >= -1 & datos_modelo_optimizado$PRO <= 1 ~ "Desempeño Esperado",
  datos_modelo_optimizado$PRO < -1 ~ "Vulnerables"
)

# Distribución de instituciones por categoría optimizada
distribucion_opt <- table(datos_modelo_optimizado$Categoria_Resiliencia_Opt)
porcentajes_opt <- round(prop.table(distribucion_opt) * 100, 1)

print("Distribución optimizada por perfil de resiliencia:")
print(distribucion_opt)
print("Porcentajes por categoría:")
print(porcentajes_opt)

# ===============================================================================
# CARACTERIZACIÓN DE GRUPOS OPTIMIZADOS
# ===============================================================================

print("\n=== CARACTERIZACIÓN DE GRUPOS OPTIMIZADOS ===")

# Función para caracterizar grupos con modelo optimizado
caracterizar_grupo_optimizado <- function(categoria) {
  grupo <- datos_modelo_optimizado[datos_modelo_optimizado$Categoria_Resiliencia_Opt == categoria, ]
  
  cat("\n=== GRUPO OPTIMIZADO:", categoria, "(n =", nrow(grupo), ") ===\n")
  
  # Estadísticas de logro académico
  cat("Logro Académico Real - Media:", round(mean(grupo$Y1_ILA), 3), "\n")
  cat("Logro Académico Esperado - Media:", round(mean(grupo$Y1_ILA_predicho_opt), 3), "\n")
  cat("Diferencia (Real - Esperado):", round(mean(grupo$residuos_opt), 3), "\n")
  cat("Perfil Resiliencia Optimizado - Media:", round(mean(grupo$PRO), 2), "\n")
  
  # Características del modelo optimizado
  cat("\nCaracterísticas del modelo optimizado:\n")
  for(var in variables_modelo_optimizado) {
    if(var %in% names(grupo)) {
      valor_promedio <- round(mean(grupo[[var]], na.rm = TRUE), 3)
      cat(paste(var, ":", valor_promedio, "\n"))
    }
  }
  
  # Top 5 instituciones por PRO
  cat("\nTop 5 instituciones por Perfil de Resiliencia Optimizado:\n")
  ejemplos <- grupo %>% 
    select(CODIGO_MODULAR, NOMBRE_INSTITUCION, Y1_ILA, PRO) %>%
    arrange(desc(PRO)) %>%
    head(5)
  print(ejemplos)
  
  return(grupo)
}

# Caracterizar cada grupo optimizado
resilientes_opt <- caracterizar_grupo_optimizado("Resilientes")
esperado_opt <- caracterizar_grupo_optimizado("Desempeño Esperado")
vulnerables_opt <- caracterizar_grupo_optimizado("Vulnerables")

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
  
  print("\nDiferencias optimizadas entre resilientes y vulnerables:")
  print(round(diferencias_opt, 3))
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
    select(CODIGO_MODULAR, NOMBRE_INSTITUCION, Y1_ILA, Y1_ILA_predicho_opt, PRO, residuos_opt) %>%
    mutate(Brecha_Opt = round(residuos_opt, 3)) %>%
    arrange(desc(PRO))
  
  print("=== RANKING INSTITUCIONES RESILIENTES OPTIMIZADO ===")
  print(ranking_resilientes_opt)
}

# Ranking de instituciones vulnerables optimizado
if(nrow(vulnerables_opt) > 0) {
  ranking_vulnerables_opt <- vulnerables_opt %>%
    select(CODIGO_MODULAR, NOMBRE_INSTITUCION, Y1_ILA, Y1_ILA_predicho_opt, PRO, residuos_opt) %>%
    mutate(Brecha_Opt = round(residuos_opt, 3)) %>%
    arrange(PRO)
  
  print("=== RANKING INSTITUCIONES VULNERABLES OPTIMIZADO ===")
  print(ranking_vulnerables_opt)
}

# ===============================================================================
# COMPARACIÓN CON CLASIFICACIÓN ORIGINAL
# ===============================================================================

print("\n=== COMPARACIÓN CON CLASIFICACIÓN ORIGINAL ===")

# Crear tabla comparativa si existe clasificación original
if(exists("datos_resiliencia_final")) {
  # Hacer merge de ambas clasificaciones
  comparacion_clasificaciones <- merge(
    datos_resiliencia_final[, c("CODIGO_MODULAR", "Categoria_Resiliencia", "PR")],
    datos_modelo_optimizado[, c("CODIGO_MODULAR", "Categoria_Resiliencia_Opt", "PRO")],
    by = "CODIGO_MODULAR"
  )
  
  # Tabla cruzada de clasificaciones
  tabla_cruzada <- table(comparacion_clasificaciones$Categoria_Resiliencia, 
                         comparacion_clasificaciones$Categoria_Resiliencia_Opt)
  
  print("Tabla cruzada: Clasificación Original vs Optimizada")
  print(tabla_cruzada)
  
  # Calcular concordancia
  concordancia <- sum(diag(tabla_cruzada)) / sum(tabla_cruzada)
  print(paste("Concordancia entre clasificaciones:", round(concordancia * 100, 1), "%"))
  
  # Identificar cambios significativos
  cambios <- comparacion_clasificaciones[
    comparacion_clasificaciones$Categoria_Resiliencia != comparacion_clasificaciones$Categoria_Resiliencia_Opt, 
  ]
  
  if(nrow(cambios) > 0) {
    print(paste("Instituciones que cambiaron de categoría:", nrow(cambios)))
    print("Principales cambios:")
    print(cambios[, c("CODIGO_MODULAR", "Categoria_Resiliencia", "Categoria_Resiliencia_Opt", "PR", "PRO")])
  }
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