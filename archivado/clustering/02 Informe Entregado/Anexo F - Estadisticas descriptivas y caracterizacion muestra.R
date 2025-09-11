# ===============================================================================
# GRÁFICOS FINALES - SECCIÓN 4.1 CARACTERIZACIÓN GENERAL DE LA MUESTRA
# Proyecto REASIS - Fe y Alegría
# ===============================================================================

# 1. CARGAR LIBRERÍAS Y DATOS
# ===============================================================================
library(readxl)
library(dplyr)
library(ggplot2)
library(gridExtra)
library(scales)

# Cargar datos (usar los datos ya cargados si están disponibles)
# Si no están disponibles, cargar nuevamente:
if(!exists("datos_instituciones")) {
  ruta_archivo <- "C:/Users/lucas/Proyectos/Reasis/archivado/clustering/01 Analisis Excel/reasis_database_v5_final.xlsx"
  datos_instituciones <- read_excel(ruta_archivo, 
                                    sheet = "instituciones_educativas",
                                    range = "A1:BC164")
}

# 2. CREAR TABLA FINAL RER CON DATOS CORRECTOS
# ===============================================================================

print("=== CREANDO TABLA FINAL RER CON DATOS CORRECTOS ===")

# Mapeo correcto de id_red_fya a información RER
tabla_rer_final <- datos_instituciones %>%
  mutate(
    codigo_red = case_when(
      id_red_fya == 39 ~ 44,
      id_red_fya == 42 ~ 47,
      id_red_fya == 43 ~ 48, 
      id_red_fya == 50 ~ 54,
      id_red_fya == 68 ~ 72,
      id_red_fya == 75 ~ 79,
      TRUE ~ NA_real_
    ),
    lugar = case_when(
      codigo_red == 44 ~ "Cusco",
      codigo_red == 47 ~ "Iquitos",
      codigo_red == 48 ~ "Malingas", 
      codigo_red == 54 ~ "Moro",
      codigo_red == 72 ~ "Pucallpa",
      codigo_red == 79 ~ "Acobamba",
      TRUE ~ "Sin definir"
    ),
    rer_completa = case_when(
      codigo_red == 44 ~ "RER 44 - Cusco",
      codigo_red == 47 ~ "RER 47 - Iquitos",
      codigo_red == 48 ~ "RER 48 - Malingas",
      codigo_red == 54 ~ "RER 54 - Moro", 
      codigo_red == 72 ~ "RER 72 - Pucallpa",
      codigo_red == 79 ~ "RER 79 - Acobamba",
      TRUE ~ "Sin RER"
    )
  ) %>%
  filter(!is.na(codigo_red)) %>%  # Excluir las 2 sin RER para el análisis
  count(codigo_red, region, lugar, rer_completa, sort = TRUE) %>%
  mutate(
    porcentaje = round(n / sum(n) * 100, 1),
    ambito = "Rural"
  ) %>%
  arrange(codigo_red)

print("Tabla RER final para el informe:")
print(tabla_rer_final)

# Verificar total
total_con_rer <- sum(tabla_rer_final$n)
print(paste("Total IIEE con RER asignada:", total_con_rer, "de 163"))

# 3. GRÁFICO 1: DISTRIBUCIÓN POR RER
# ===============================================================================

print("\n=== GENERANDO GRÁFICO 1: DISTRIBUCIÓN POR RER ===")

# Preparar datos para gráfico de barras RER
datos_grafico_rer <- tabla_rer_final %>%
  mutate(
    etiqueta_rer = paste0("RER ", codigo_red, "\n", lugar),
    etiqueta_completa = paste0(n, " IIEE\n(", porcentaje, "%)")
  )

# Crear gráfico de barras para RER
grafico_rer <- ggplot(datos_grafico_rer, 
                      aes(x = reorder(etiqueta_rer, -n), y = n, fill = etiqueta_rer)) +
  geom_col(alpha = 0.8, width = 0.7, color = "white", size = 0.5) +
  geom_text(aes(label = etiqueta_completa), 
            vjust = -0.3, size = 3.5, fontface = "bold", color = "black") +
  scale_fill_brewer(type = "qual", palette = "Set2") +
  scale_y_continuous(limits = c(0, max(datos_grafico_rer$n) * 1.15),
                     breaks = seq(0, 50, 10)) +
  labs(
    title = "Distribución de Instituciones Educativas por Red Educativa Rural (RER)",
    subtitle = "Fe y Alegría | Total: 161 IIEE",
    x = "Red Educativa Rural",
    y = "Número de Instituciones Educativas",
    caption = "Fuente: Fe y alegria, Julio 2025"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(size = 14, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(size = 11, hjust = 0.5, color = "gray40"), 
    axis.title = element_text(size = 11, face = "bold"),
    axis.text.x = element_text(size = 10, face = "bold"),
    axis.text.y = element_text(size = 10),
    legend.position = "none",
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank(),
    plot.caption = element_text(size = 9, color = "gray50")
  )

print("Gráfico RER generado exitosamente")
print(grafico_rer)

# 4. GRÁFICO 2: DISTRIBUCIÓN GEOGRÁFICA POR REGIÓN  
# ===============================================================================

print("\n=== GENERANDO GRÁFICO 2: DISTRIBUCIÓN GEOGRÁFICA ===")

# Preparar datos por región
datos_region <- datos_instituciones %>%
  count(region, sort = TRUE) %>%
  mutate(
    porcentaje = round(n / sum(n) * 100, 1),
    etiqueta = paste0(n, " IIEE\n(", porcentaje, "%)")
  )

# Crear gráfico de barras horizontales para regiones
grafico_region <- ggplot(datos_region, 
                         aes(x = reorder(region, n), y = n, fill = region)) +
  geom_col(alpha = 0.8, width = 0.7, color = "white", size = 0.5) +
  geom_text(aes(label = etiqueta), 
            hjust = -0.1, size = 3.5, fontface = "bold", color = "black") +
  scale_fill_brewer(type = "qual", palette = "Set1") +
  scale_y_continuous(limits = c(0, max(datos_region$n) * 1.2),
                     breaks = seq(0, 50, 10)) +
  coord_flip() +
  labs(
    title = "Distribución Geográfica de Instituciones Educativas por Región",
    subtitle = "Fe y Alegría | Total: 163 IIEE",
    x = "Región",
    y = "Número de Instituciones Educativas", 
    caption = "Fuente: Fe y alegria, Julio 2025"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(size = 14, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(size = 11, hjust = 0.5, color = "gray40"),
    axis.title = element_text(size = 11, face = "bold"),
    axis.text = element_text(size = 10, face = "bold"),
    legend.position = "none",
    panel.grid.major.y = element_blank(),
    panel.grid.minor = element_blank(),
    plot.caption = element_text(size = 9, color = "gray50")
  )

print("Gráfico de distribución geográfica generado exitosamente")
print(grafico_region)

# 5. TABLA RESUMEN PARA EL INFORME
# ===============================================================================

print("\n=== TABLA RESUMEN PARA EL INFORME ===")

# Crear tabla resumen final con formato para informe
tabla_resumen_informe <- tabla_rer_final %>%
  select(codigo_red, region, lugar, ambito, n) %>%
  rename(
    "Código RER" = codigo_red,
    "Región" = region, 
    "Lugar" = lugar,
    "Ámbito" = ambito,
    "Cantidad IIEE" = n
  ) %>%
  arrange(`Código RER`)

print("Tabla resumen final para el informe:")
print(tabla_resumen_informe)

# Exportar tabla a CSV para fácil copia al informe
write.csv(tabla_resumen_informe, "tabla_rer_resumen_informe.csv", row.names = FALSE)
print("Tabla exportada a: tabla_rer_resumen_informe.csv")

# 6. ESTADÍSTICAS ADICIONALES PARA EL INFORME
# ===============================================================================

print("\n=== ESTADÍSTICAS ADICIONALES PARA EL INFORME ===")

# Estadísticas generales
total_iiee <- nrow(datos_instituciones)
iiee_rurales <- sum(datos_instituciones$es_rural == 1, na.rm = TRUE)
iiee_urbanas <- sum(datos_instituciones$es_rural == 0, na.rm = TRUE)
porcentaje_rural <- round(iiee_rurales / total_iiee * 100, 1)

print("ESTADÍSTICAS GENERALES:")
print(paste("• Total de instituciones educativas:", total_iiee))
print(paste("• Instituciones rurales:", iiee_rurales, "(", porcentaje_rural, "%)"))
print(paste("• Instituciones urbanas:", iiee_urbanas, "(", round(100-porcentaje_rural, 1), "%)"))
print(paste("• Número de regiones cubiertas:", length(unique(datos_instituciones$region))))
print(paste("• Número de RER activas:", nrow(tabla_rer_final)))

# Distribución por código modular único
print("\nCARACTERÍSTICAS DE LOS CÓDIGOS MODULARES:")
print("• Cada código modular es único por servicio educativo")
print("• Las IIEE que ofrecen múltiples niveles aparecen con códigos separados")
print("• Total de servicios educativos registrados: 163")

print("\n=== ANÁLISIS COMPLETADO PARA SECCIÓN 4.1 ===")
print("Gráficos y tablas listos para incluir en el informe")

















# ===============================================================================
# CÓDIGO ADICIONAL - DISTRIBUCIÓN POR NIVEL EDUCATIVO
# Agregar después de la línea 192 del código existente
# ===============================================================================

# 7. ANÁLISIS DE DISTRIBUCIÓN POR NIVEL EDUCATIVO
# ===============================================================================

print("\n=== ANÁLISIS DE DISTRIBUCIÓN POR NIVEL EDUCATIVO ===")

# Explorar valores únicos de nivel educativo
print("Valores únicos en nivel_educativo:")
niveles_unicos <- unique(datos_instituciones$nivel_educativo)
print(niveles_unicos)

# Crear distribución por nivel educativo
datos_nivel_educativo <- datos_instituciones %>%
  count(nivel_educativo, sort = TRUE) %>%
  mutate(
    porcentaje = round(n / sum(n) * 100, 1),
    etiqueta = paste0(n, " IIEE\n(", porcentaje, "%)")
  )

print("Distribución por nivel educativo:")
print(datos_nivel_educativo)

# 8. GRÁFICO 3: DISTRIBUCIÓN POR NIVEL EDUCATIVO
# ===============================================================================

print("\n=== GENERANDO GRÁFICO 3: DISTRIBUCIÓN POR NIVEL EDUCATIVO ===")

# Crear gráfico de barras para nivel educativo
grafico_nivel <- ggplot(datos_nivel_educativo, 
                        aes(x = reorder(nivel_educativo, n), y = n, fill = nivel_educativo)) +
  geom_col(alpha = 0.8, width = 0.7, color = "white", size = 0.5) +
  geom_text(aes(label = etiqueta), 
            hjust = -0.1, size = 3.2, fontface = "bold", color = "black") +
  scale_fill_brewer(type = "qual", palette = "Spectral") +
  scale_y_continuous(limits = c(0, max(datos_nivel_educativo$n) * 1.2),
                     breaks = seq(0, max(datos_nivel_educativo$n), 10)) +
  coord_flip() +
  labs(
    title = "Distribución de Instituciones Educativas por Nivel Educativo",
    subtitle = "Fe y Alegría | Total: 163 IIEE",
    x = "Nivel Educativo",
    y = "Número de Instituciones Educativas",
    caption = "Fuente: Fe y alegria, Julio 2025"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(size = 14, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(size = 11, hjust = 0.5, color = "gray40"),
    axis.title = element_text(size = 11, face = "bold"),
    axis.text = element_text(size = 9, face = "bold"),
    legend.position = "none",
    panel.grid.major.y = element_blank(),
    panel.grid.minor = element_blank(),
    plot.caption = element_text(size = 9, color = "gray50")
  )

print("Gráfico de distribución por nivel educativo generado exitosamente")
print(grafico_nivel)

# 9. TABLA RESUMEN NIVEL EDUCATIVO PARA EL INFORME
# ===============================================================================

print("\n=== TABLA RESUMEN NIVEL EDUCATIVO PARA EL INFORME ===")

# Crear tabla resumen para el informe
tabla_nivel_informe <- datos_nivel_educativo %>%
  rename(
    "Nivel Educativo" = nivel_educativo,
    "Cantidad IIEE" = n,
    "Porcentaje" = porcentaje
  ) %>%
  arrange(desc(`Cantidad IIEE`))

print("Tabla resumen por nivel educativo:")
print(tabla_nivel_informe)

# Exportar tabla a CSV
write.csv(tabla_nivel_informe, "tabla_nivel_educativo_resumen.csv", row.names = FALSE)
print("Tabla exportada a: tabla_nivel_educativo_resumen.csv")

# 10. ESTADÍSTICAS ADICIONALES POR NIVEL EDUCATIVO
# ===============================================================================

print("\n=== ESTADÍSTICAS ADICIONALES POR NIVEL EDUCATIVO ===")

# Agrupar niveles similares para mejor interpretación
datos_nivel_agrupado <- datos_instituciones %>%
  mutate(
    nivel_agrupado = case_when(
      str_detect(nivel_educativo, "Inicial") ~ "Inicial",
      str_detect(nivel_educativo, "Primaria") ~ "Primaria", 
      str_detect(nivel_educativo, "Secundaria") ~ "Secundaria",
      str_detect(nivel_educativo, "Instituto") ~ "Superior",
      str_detect(nivel_educativo, "Básica Especial") ~ "Educación Especial",
      TRUE ~ "Otros"
    )
  ) %>%
  count(nivel_agrupado, sort = TRUE) %>%
  mutate(porcentaje = round(n / sum(n) * 100, 1))

print("DISTRIBUCIÓN POR NIVEL AGRUPADO:")
for(i in 1:nrow(datos_nivel_agrupado)) {
  print(paste("•", datos_nivel_agrupado$nivel_agrupado[i], ":", 
              datos_nivel_agrupado$n[i], "IIEE (", 
              datos_nivel_agrupado$porcentaje[i], "%)"))
}

# Características del sistema multinivel
instituciones_multinivel <- datos_instituciones %>%
  group_by(codigo_local) %>%
  summarise(
    niveles_count = n(),
    niveles_list = paste(nivel_educativo, collapse = ", "),
    .groups = 'drop'
  ) %>%
  count(niveles_count) %>%
  mutate(porcentaje = round(n / sum(n) * 100, 1))

print("\nCARACTERÍSTICAS MULTINIVEL:")
print("• Instituciones por número de niveles ofrecidos:")
for(i in 1:nrow(instituciones_multinivel)) {
  if(instituciones_multinivel$niveles_count[i] == 1) {
    print(paste("  - Un solo nivel:", instituciones_multinivel$n[i], 
                "locales (", instituciones_multinivel$porcentaje[i], "%)"))
  } else {
    print(paste("  -", instituciones_multinivel$niveles_count[i], "niveles:", 
                instituciones_multinivel$n[i], "locales (", 
                instituciones_multinivel$porcentaje[i], "%)"))
  }
}

print("\n=== ANÁLISIS DE NIVEL EDUCATIVO COMPLETADO ===")
print("Gráfico y tablas de nivel educativo listos para incluir en el informe")













# ===============================================================================
# ANÁLISIS NIVEL EDUCATIVO - BASE DE DATOS CORRECTA
# Usando archivo: IIEE CONFIRMADAS POR RER FE Y ALEGRIA.xlsx
# ===============================================================================

library(readxl)
library(dplyr)
library(ggplot2)
library(stringr)

# 1. CARGAR DATOS DE LA BASE CORRECTA
# ===============================================================================

print("=== CARGANDO DATOS DE LA BASE CORRECTA ===")

# Ruta del archivo correcto
ruta_archivo_iiee <- "C:/Users/lucas/Proyectos/Reasis/data/bases_de_datos/IIEE CONFIRMADAS POR RER FE Y ALEGRIA.xlsx"

# Cargar datos del sheet "Instituciones Educativas"
datos_iiee_completos <- read_excel(ruta_archivo_iiee, sheet = "Instituciones Educativas")

print(paste("Datos cargados:", nrow(datos_iiee_completos), "filas x", ncol(datos_iiee_completos), "columnas"))

# Verificar nombres de columnas
print("Nombres de columnas disponibles:")
print(colnames(datos_iiee_completos))

# 2. VERIFICAR Y LIMPIAR DATOS DE NIVEL EDUCATIVO
# ===============================================================================

print("\n=== VERIFICANDO DATOS DE NIVEL EDUCATIVO ===")

# Verificar la columna de nivel educativo
if("Nivel Educativo/Modalidad" %in% colnames(datos_iiee_completos)) {
  print("Valores únicos en 'Nivel Educativo/Modalidad':")
  niveles_unicos <- unique(datos_iiee_completos$`Nivel Educativo/Modalidad`)
  print(niveles_unicos[!is.na(niveles_unicos)])
  
  # Mostrar tabla de frecuencias
  print("\nTabla de frecuencias:")
  print(table(datos_iiee_completos$`Nivel Educativo/Modalidad`, useNA = "ifany"))
} else {
  print("ERROR: Columna 'Nivel Educativo/Modalidad' no encontrada")
  print("Columnas disponibles que contienen 'nivel' o 'educativ':")
  cols_relevantes <- colnames(datos_iiee_completos)[grepl("nivel|educativ", colnames(datos_iiee_completos), ignore.case = TRUE)]
  print(cols_relevantes)
}

# 3. VERIFICAR Y PROCESAR DATOS DE RER
# ===============================================================================

print("\n=== VERIFICANDO DATOS DE RER ===")

if("N° FYA" %in% colnames(datos_iiee_completos)) {
  print("Valores únicos en 'N° FYA':")
  rer_valores <- unique(datos_iiee_completos$`N° FYA`)
  print(rer_valores[!is.na(rer_valores)])
  
  # Extraer números de RER
  datos_iiee_procesados <- datos_iiee_completos %>%
    mutate(
      codigo_rer = str_extract(`N° FYA`, "\\d{2}$"),  # Extraer últimos 2 dígitos
      codigo_rer_num = as.numeric(codigo_rer),
      nivel_educativo_limpio = `Nivel Educativo/Modalidad`
    ) %>%
    filter(!is.na(nivel_educativo_limpio), !is.na(codigo_rer_num))
  
  print(paste("\nDatos procesados:", nrow(datos_iiee_procesados), "instituciones con datos completos"))
  
} else {
  print("ERROR: Columna 'N° FYA' no encontrada")
  print("Columnas disponibles que contienen 'fya' o 'rer':")
  cols_rer <- colnames(datos_iiee_completos)[grepl("fya|rer", colnames(datos_iiee_completos), ignore.case = TRUE)]
  print(cols_rer)
}

# 4. ANÁLISIS DE DISTRIBUCIÓN POR NIVEL EDUCATIVO
# ===============================================================================

print("\n=== ANÁLISIS DE DISTRIBUCIÓN POR NIVEL EDUCATIVO ===")

if(exists("datos_iiee_procesados") && nrow(datos_iiee_procesados) > 0) {
  
  # Crear distribución por nivel educativo
  distribucion_nivel <- datos_iiee_procesados %>%
    count(nivel_educativo_limpio, sort = TRUE) %>%
    mutate(
      porcentaje = round(n / sum(n) * 100, 1),
      etiqueta = paste0(n, " IIEE\n(", porcentaje, "%)")
    )
  
  print("Distribución por nivel educativo:")
  print(distribucion_nivel)
  
  # 5. GRÁFICO DE DISTRIBUCIÓN POR NIVEL EDUCATIVO
  # ===============================================================================
  
  print("\n=== GENERANDO GRÁFICO DE NIVEL EDUCATIVO ===")
  
  # Crear gráfico de barras
  grafico_nivel_correcto <- ggplot(distribucion_nivel, 
                                   aes(x = reorder(nivel_educativo_limpio, n), 
                                       y = n, 
                                       fill = nivel_educativo_limpio)) +
    geom_col(alpha = 0.8, width = 0.7, color = "white", size = 0.5) +
    geom_text(aes(label = etiqueta), 
              hjust = -0.1, size = 3.5, fontface = "bold", color = "black") +
    scale_fill_brewer(type = "qual", palette = "Set3") +
    scale_y_continuous(limits = c(0, max(distribucion_nivel$n) * 1.2),
                       breaks = seq(0, max(distribucion_nivel$n), 10)) +
    coord_flip() +
    labs(
      title = "Distribución de Instituciones Educativas por Nivel Educativo",
      subtitle = paste("Fe y Alegría | Total:", sum(distribucion_nivel$n), "IIEE"),
      x = "Nivel Educativo",
      y = "Número de Instituciones Educativas",
      caption = "Fuente: IIEE Confirmadas por RER Fe y Alegría 2025"
    ) +
    theme_minimal() +
    theme(
      plot.title = element_text(size = 14, face = "bold", hjust = 0.5),
      plot.subtitle = element_text(size = 11, hjust = 0.5, color = "gray40"),
      axis.title = element_text(size = 11, face = "bold"),
      axis.text = element_text(size = 10, face = "bold"),
      legend.position = "none",
      panel.grid.major.y = element_blank(),
      panel.grid.minor = element_blank(),
      plot.caption = element_text(size = 9, color = "gray50")
    )
  
  print("Gráfico generado exitosamente")
  print(grafico_nivel_correcto)
  
  # 6. ANÁLISIS CRUZADO: NIVEL EDUCATIVO POR RER
  # ===============================================================================
  
  print("\n=== ANÁLISIS CRUZADO: NIVEL EDUCATIVO POR RER ===")
  
  # Mapeo de códigos RER a nombres para consistency con análisis anterior
  mapeo_rer <- data.frame(
    codigo_rer_num = c(44, 47, 48, 54, 72, 79),
    nombre_rer = c("RER 44 - Cusco", "RER 47 - Iquitos", "RER 48 - Malingas", 
                   "RER 54 - Moro", "RER 72 - Pucallpa", "RER 79 - Acobamba")
  )
  
  # Análisis cruzado
  analisis_cruzado <- datos_iiee_procesados %>%
    left_join(mapeo_rer, by = "codigo_rer_num") %>%
    count(nombre_rer, nivel_educativo_limpio) %>%
    group_by(nombre_rer) %>%
    mutate(
      porcentaje_rer = round(n / sum(n) * 100, 1),
      total_rer = sum(n)
    ) %>%
    ungroup()
  
  print("Distribución de niveles educativos por RER:")
  print(analisis_cruzado)
  
  # 7. TABLA RESUMEN PARA EL INFORME
  # ===============================================================================
  
  print("\n=== TABLA RESUMEN PARA EL INFORME ===")
  
  # Crear tabla resumen final
  tabla_nivel_final <- distribucion_nivel %>%
    rename(
      "Nivel Educativo" = nivel_educativo_limpio,
      "Cantidad IIEE" = n,
      "Porcentaje" = porcentaje
    ) %>%
    select(-etiqueta) %>%
    arrange(desc(`Cantidad IIEE`))
  
  print("Tabla resumen final por nivel educativo:")
  print(tabla_nivel_final)
  
  # Exportar tabla
  write.csv(tabla_nivel_final, "tabla_nivel_educativo_final.csv", row.names = FALSE)
  print("Tabla exportada a: tabla_nivel_educativo_final.csv")
  
  # 8. ESTADÍSTICAS RESUMIDAS PARA EL INFORME
  # ===============================================================================
  
  print("\n=== ESTADÍSTICAS RESUMIDAS ===")
  
  total_instituciones <- sum(distribucion_nivel$n)
  print(paste("• Total de instituciones educativas:", total_instituciones))
  
  for(i in 1:nrow(tabla_nivel_final)) {
    print(paste("•", tabla_nivel_final$`Nivel Educativo`[i], ":", 
                tabla_nivel_final$`Cantidad IIEE`[i], "IIEE (", 
                tabla_nivel_final$Porcentaje[i], "%)"))
  }
  
  # Calcular estadísticas adicionales
  inicial_total <- sum(tabla_nivel_final$`Cantidad IIEE`[grepl("Inicial", tabla_nivel_final$`Nivel Educativo`)])
  inicial_porcentaje <- round(inicial_total / total_instituciones * 100, 1)
  
  print(paste("\n• Total Educación Inicial (combinada):", inicial_total, "IIEE (", inicial_porcentaje, "%)"))
  
} else {
  print("ERROR: No se pudieron procesar los datos. Verificar estructura del archivo.")
}

print("\n=== ANÁLISIS DE NIVEL EDUCATIVO COMPLETADO ===")
print("Usar los resultados para actualizar la sección 4.1 del informe")