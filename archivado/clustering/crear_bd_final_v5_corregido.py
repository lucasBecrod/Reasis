#!/usr/bin/env python3
"""
Crear base de datos final v5 con solo tablas esenciales - VERSION CORREGIDA
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

def crear_bd_v5_directo():
    """Crear BD v5 directamente con tablas específicas"""
    
    conn_v4 = sqlite3.connect('reasis_database_v4.db')
    conn_v5 = sqlite3.connect('reasis_database_v5.db')
    
    print("=== CREANDO BASE DE DATOS FINAL V5 ===")
    
    # Tablas esenciales definidas
    tablas_esenciales = [
        'indices_metodologicos',     # Tabla principal clustering
        'instituciones_educativas',  # Datos maestros
        'resultados_academicos',     # Fuente Y1_ILA
        'datos_eib_minedu',         # Fuente X1_NVC, X15_MEIB
        'x5_ed_estabilidad_docente', # Fuente X5_ED
        'datos_toe_servicios_2024',  # Fuente X12_TOE
        'docentes_data',            # Fuente X4_IDD
        'competencia_digital_docentes', # Fuente X6_CDD
        'redes_fe_y_alegria',       # Referencias oficiales
        'mapeo_codigos_ie'          # Validación cruzada
    ]
    
    total_registros = 0
    tablas_copiadas = 0
    
    for tabla in tablas_esenciales:
        try:
            # Verificar existencia
            df_check = pd.read_sql_query(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabla}'", conn_v4)
            if len(df_check) == 0:
                print(f"  [SKIP] {tabla}: no existe")
                continue
            
            # Copiar tabla completa
            df = pd.read_sql_query(f"SELECT * FROM {tabla}", conn_v4)
            df.to_sql(tabla, conn_v5, if_exists='replace', index=False)
            
            print(f"  [OK] {tabla}: {len(df)} registros")
            total_registros += len(df)
            tablas_copiadas += 1
            
        except Exception as e:
            print(f"  [ERROR] {tabla}: {e}")
    
    # Crear metadatos
    metadatos = pd.DataFrame({
        'propiedad': ['version', 'fecha_creacion', 'tablas_incluidas', 'total_registros', 'objetivo'],
        'valor': [
            '5.0',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            tablas_copiadas,
            total_registros,
            'Clustering K-Means 163 instituciones RER'
        ]
    })
    metadatos.to_sql('metadatos_v5', conn_v5, if_exists='replace', index=False)
    
    conn_v4.close()
    conn_v5.commit()
    conn_v5.close()
    
    print(f"\n[COMPLETADO] BD v5 creada:")
    print(f"  Archivo: reasis_database_v5.db")
    print(f"  Tablas: {tablas_copiadas}")
    print(f"  Registros: {total_registros:,}")
    
    return total_registros

def exportar_excel_para_r():
    """Exportar a Excel optimizado para R Studio"""
    
    conn = sqlite3.connect('reasis_database_v5.db')
    
    print("\n=== EXPORTANDO A EXCEL PARA R STUDIO ===")
    
    archivo_excel = 'reasis_database_v5_final.xlsx'
    
    try:
        with pd.ExcelWriter(archivo_excel, engine='openpyxl') as writer:
            
            # 1. HOJA PRINCIPAL: índices metodológicos (para clustering)
            df_indices = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
            df_indices.to_excel(writer, sheet_name='indices_metodologicos', index=False)
            print(f"  [PRINCIPAL] indices_metodologicos: {len(df_indices)} filas, {len(df_indices.columns)} columnas")
            
            # 2. HOJA CONTEXTO: instituciones educativas
            df_ie = pd.read_sql_query("SELECT * FROM instituciones_educativas", conn)
            df_ie.to_excel(writer, sheet_name='instituciones_educativas', index=False)
            print(f"  [CONTEXTO] instituciones_educativas: {len(df_ie)} filas")
            
            # 3. HOJAS DE VALIDACIÓN (muestras)
            tablas_fuentes = {
                'resultados_academicos': 5000,  # Muestra académica
                'datos_eib_minedu': 100,        # Datos EIB completos
                'x5_ed_estabilidad_docente': 100, # Estabilidad docente
                'datos_toe_servicios_2024': 200,  # TOE
                'docentes_data': 500,             # PADD docentes
                'redes_fe_y_alegria': 10         # Redes oficiales
            }
            
            for tabla, limite in tablas_fuentes.items():
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {tabla} LIMIT {limite}", conn)
                    if len(df) > 0:
                        df.to_excel(writer, sheet_name=tabla[:31], index=False)  # Excel limit 31 chars
                        print(f"  [FUENTE] {tabla}: {len(df)} filas")
                except:
                    print(f"  [SKIP] {tabla}: no disponible")
            
            # 4. GUÍA PARA R STUDIO
            guia = pd.DataFrame({
                'Elemento': [
                    'HOJA_PRINCIPAL',
                    'VARIABLES_Y',
                    'VARIABLES_X_PRINCIPALES', 
                    'VARIABLES_X_CONTEXTO',
                    'CODIGO_IDENTIFICADOR',
                    'TOTAL_INSTITUCIONES',
                    'METODO_RECOMENDADO',
                    'K_SUGERIDO'
                ],
                'Descripcion': [
                    'indices_metodologicos - Usar para clustering',
                    'Y1_ILA, Y2_TD, Y3_PR - Variables dependientes',
                    'X1_NVC, X2_TR, X4_IDD, X5_ED, X6_CDD - Variables clave',
                    'X10_IE, X11_RED, X12_TOE, X13_TMATRC, X15_MEIB, X24_GPMD',
                    'CODIGO_MODULAR - Identificador único instituciones',
                    '163 instituciones RER oficiales',
                    'K-Means con estandarización (scale)',
                    'k=4 a k=8 (determinar con elbow/silhouette)'
                ]
            })
            guia.to_excel(writer, sheet_name='GUIA_R', index=False)
            print(f"  [GUIA] Instrucciones para R incluidas")
            
        # Verificar archivo
        if os.path.exists(archivo_excel):
            size_mb = os.path.getsize(archivo_excel) / (1024*1024)
            print(f"\n[EXITO] Excel creado: {archivo_excel} ({size_mb:.1f} MB)")
        else:
            print(f"\n[ERROR] No se creó {archivo_excel}")
            
    except Exception as e:
        print(f"[ERROR EXCEL] {e}")
    
    conn.close()
    return archivo_excel

def crear_script_r_completo():
    """Crear script R completo para clustering"""
    
    script_r = '''# CLUSTERING K-MEANS PROYECTO REASIS
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
'''
    
    with open('clustering_kmeans_reasis_completo.R', 'w', encoding='utf-8') as f:
        f.write(script_r)
    
    print(f"\n[SCRIPT R] clustering_kmeans_reasis_completo.R creado")

def main():
    """Función principal"""
    
    print("CREAR BASE DE DATOS FINAL V5 PARA CLUSTERING K-MEANS")
    print("=" * 60)
    
    try:
        # 1. Crear BD v5 limpia
        total_registros = crear_bd_v5_directo()
        
        # 2. Exportar a Excel para R
        archivo_excel = exportar_excel_para_r()
        
        # 3. Crear script R completo
        crear_script_r_completo()
        
        print("\n" + "=" * 60)
        print("[COMPLETADO] ENTREGABLES FINALES LISTOS")
        print(f"[BD FINAL] reasis_database_v5.db - Base limpia y optimizada")
        print(f"[EXCEL R] {archivo_excel} - Datos para R Studio")
        print(f"[SCRIPT R] clustering_kmeans_reasis_completo.R - Código completo")
        print(f"[GUIA] PASOS_KMEANS_RSTUDIO.md - Documentación detallada")
        print(f"\n[DATOS] 163 instituciones RER con 23 variables metodológicas")
        print(f"[LISTO] Para ejecutar clustering K-Means en R Studio")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()