#!/usr/bin/env python3
"""
Crear base de datos final v5 con solo tablas esenciales para clustering
+ Exportar a Excel para análisis en R Studio
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

def identificar_tablas_esenciales():
    """Identificar qué tablas son esenciales para el estudio"""
    
    conn = sqlite3.connect('reasis_database_v4.db')
    
    print("=== IDENTIFICANDO TABLAS ESENCIALES ===")
    
    # Obtener lista de todas las tablas
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    todas_tablas = [row[0] for row in cursor.fetchall()]
    
    print(f"Total tablas en v4: {len(todas_tablas)}")
    
    # Clasificar tablas
    tablas_esenciales = {
        # Tabla principal del clustering
        'indices_metodologicos': 'Tabla principal con todas las variables metodológicas',
        'instituciones_educativas': 'Datos maestros de instituciones con información contextual',
        
        # Fuentes de datos originales (para validación)
        'resultados_academicos': 'Fuente original Y1_ILA - 15,054 estudiantes evaluados',
        'datos_eib_minedu': 'Fuente X1_NVC, X15_MEIB - Datos oficiales MINEDU EIB',
        'x5_ed_estabilidad_docente': 'Fuente X5_ED - Estabilidad docente nombrados/contratados',
        'datos_toe_servicios_2024': 'Fuente X12_TOE - Tipo organización escolar',
        'docentes_data': 'Fuente X4_IDD - Evaluaciones PADD docentes',
        'competencia_digital_docentes': 'Fuente X6_CDD - Competencia digital',
        
        # Referencias oficiales
        'redes_fe_y_alegria': 'Definición oficial de las 6 redes del estudio',
        'mapeo_codigos_ie': 'Equivalencias códigos para validación cruzada'
    }
    
    # Identificar tablas a excluir
    tablas_excluir = []
    for tabla in todas_tablas:
        if any(keyword in tabla.lower() for keyword in ['backup', 'temp', 'old', 'v3', 'clustering', 'zscore']):
            tablas_excluir.append(tabla)
    
    print(f"\nTablas esenciales seleccionadas: {len(tablas_esenciales)}")
    for tabla, desc in tablas_esenciales.items():
        if tabla in todas_tablas:
            print(f"  ✓ {tabla}: {desc}")
        else:
            print(f"  ✗ {tabla}: NO EXISTE")
    
    print(f"\nTablas a excluir: {len(tablas_excluir)}")
    for tabla in tablas_excluir[:10]:  # Mostrar solo primeras 10
        print(f"  - {tabla}")
    
    conn.close()
    return list(tablas_esenciales.keys()), tablas_excluir

def crear_bd_v5(tablas_esenciales):
    """Crear nueva base de datos v5 con solo tablas esenciales"""
    
    conn_v4 = sqlite3.connect('reasis_database_v4.db')
    conn_v5 = sqlite3.connect('reasis_database_v5.db')
    
    print("\n=== CREANDO BASE DE DATOS V5 ===")
    print("Archivo: reasis_database_v5.db")
    
    cursor_v4 = conn_v4.cursor()
    cursor_v5 = conn_v5.cursor()
    
    total_registros = 0
    
    for tabla in tablas_esenciales:
        try:
            # Verificar si la tabla existe en v4
            cursor_v4.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{tabla}'")
            if cursor_v4.fetchone()[0] == 0:
                print(f"  [SKIP] {tabla}: no existe en v4")
                continue
            
            # Obtener estructura de la tabla
            cursor_v4.execute(f"PRAGMA table_info({tabla})")
            estructura = cursor_v4.fetchall()
            
            # Crear tabla en v5
            columnas_def = []
            for col in estructura:
                columnas_def.append(f"{col[1]} {col[2]}")
            
            create_query = f"CREATE TABLE {tabla} ({', '.join(columnas_def)})"
            cursor_v5.execute(create_query)
            
            # Copiar datos
            df = pd.read_sql_query(f"SELECT * FROM {tabla}", conn_v4)
            df.to_sql(tabla, conn_v5, if_exists='replace', index=False)
            
            print(f"  [OK] {tabla}: {len(df)} registros copiados")
            total_registros += len(df)
            
        except Exception as e:
            print(f"  [ERROR] {tabla}: {e}")
    
    # Crear tabla de metadatos
    metadatos = {
        'tabla': ['metadatos_bd_v5'],
        'descripcion': ['Base de datos final para clustering K-Means - Solo tablas esenciales'],
        'fecha_creacion': [datetime.now().isoformat()],
        'version': ['5.0'],
        'total_tablas': [len(tablas_esenciales)],
        'total_registros': [total_registros],
        'objetivo': ['Clustering K-Means con 163 instituciones RER y 23 variables metodológicas']
    }
    
    df_metadatos = pd.DataFrame(metadatos)
    df_metadatos.to_sql('metadatos_bd_v5', conn_v5, if_exists='replace', index=False)
    
    conn_v4.close()
    conn_v5.commit()
    conn_v5.close()
    
    print(f"\n[COMPLETADO] Base de datos v5 creada")
    print(f"  Total tablas: {len(tablas_esenciales) + 1} (+ metadatos)")
    print(f"  Total registros: {total_registros:,}")
    
    return total_registros

def exportar_a_excel():
    """Exportar BD v5 a Excel para análisis en R Studio"""
    
    conn = sqlite3.connect('reasis_database_v5.db')
    
    print("\n=== EXPORTANDO A EXCEL PARA R STUDIO ===")
    
    archivo_excel = 'reasis_database_v5_final.xlsx'
    
    # Obtener lista de tablas
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = [row[0] for row in cursor.fetchall()]
    
    with pd.ExcelWriter(archivo_excel, engine='openpyxl') as writer:
        
        # Hoja principal: índices metodológicos (para clustering)
        df_indices = pd.read_sql_query("SELECT * FROM indices_metodologicos", conn)
        df_indices.to_excel(writer, sheet_name='indices_metodologicos', index=False)
        print(f"  [OK] indices_metodologicos: {len(df_indices)} registros")
        
        # Hoja de instituciones (información contextual)
        df_instituciones = pd.read_sql_query("SELECT * FROM instituciones_educativas", conn)
        df_instituciones.to_excel(writer, sheet_name='instituciones_educativas', index=False)
        print(f"  [OK] instituciones_educativas: {len(df_instituciones)} registros")
        
        # Tablas de fuentes (para validación)
        tablas_fuentes = [
            'resultados_academicos', 'datos_eib_minedu', 'x5_ed_estabilidad_docente',
            'datos_toe_servicios_2024', 'docentes_data', 'competencia_digital_docentes',
            'redes_fe_y_alegria', 'mapeo_codigos_ie'
        ]
        
        for tabla in tablas_fuentes:
            if tabla in tablas:
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {tabla}", conn)
                    # Limitar tamaño de hoja (Excel tiene límite de ~1M filas)
                    if len(df) > 50000:
                        df_sample = df.head(50000)
                        sheet_name = f"{tabla}_sample"
                        print(f"  [SAMPLE] {tabla}: {len(df_sample)} de {len(df)} registros")
                    else:
                        df_sample = df
                        sheet_name = tabla
                        print(f"  [OK] {tabla}: {len(df_sample)} registros")
                    
                    df_sample.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                except Exception as e:
                    print(f"  [ERROR] {tabla}: {e}")
        
        # Hoja de metadatos
        df_metadatos = pd.read_sql_query("SELECT * FROM metadatos_bd_v5", conn)
        df_metadatos.to_excel(writer, sheet_name='metadatos', index=False)
        print(f"  [OK] metadatos: {len(df_metadatos)} registros")
        
        # Hoja de guía para R
        guia_r = pd.DataFrame({
            'Hoja': ['indices_metodologicos', 'instituciones_educativas', 'resultados_academicos', 'datos_eib_minedu'],
            'Propósito': [
                'TABLA PRINCIPAL para clustering K-Means - 163 instituciones, 23 variables',
                'Información contextual y validación cruzada',
                'Fuente original Y1_ILA - Datos académicos estudiantes',
                'Fuente X1_NVC, X15_MEIB - Datos oficiales EIB MINEDU'
            ],
            'Variables_Clave': [
                'Y1_ILA, Y2_TD, Y3_PR, X1_NVC-X25_POBLACION_DISTRITO',
                'codigo_modular, nombre_institucion, region, distrito',
                'codigo_modular_ie, competencia, area_curricular',
                'codigo_modular, quintil_pobreza, modalidad_eib'
            ]
        })
        guia_r.to_excel(writer, sheet_name='GUIA_R_STUDIO', index=False)
    
    # Verificar archivo creado
    if os.path.exists(archivo_excel):
        size_mb = os.path.getsize(archivo_excel) / (1024*1024)
        print(f"\n[EXITO] Archivo Excel creado: {archivo_excel}")
        print(f"  Tamaño: {size_mb:.1f} MB")
        print(f"  Listo para análisis en R Studio")
    else:
        print(f"\n[ERROR] No se pudo crear {archivo_excel}")
    
    conn.close()
    return archivo_excel

def generar_script_r_basico():
    """Generar script R básico para cargar datos"""
    
    script_r = '''# SCRIPT R PARA CLUSTERING K-MEANS - PROYECTO REASIS
# Archivo generado automáticamente

# Cargar librerías necesarias
library(readxl)
library(dplyr)
library(cluster)
library(factoextra)
library(ggplot2)

# Cargar datos principales
datos <- read_excel("reasis_database_v5_final.xlsx", sheet = "indices_metodologicos")

# Verificar estructura
str(datos)
summary(datos)

# Variables para clustering (seleccionar según necesidad)
vars_clustering <- datos %>%
  select(Y1_ILA, Y2_TD, Y3_PR,                    # Variables dependientes
         X1_NVC, X2_TR, X4_IDD, X5_ED, X6_CDD,    # Variables contextuales principales
         X10_IE, X11_RED, X12_TOE, X13_TMATRC,    # Variables organizacionales
         X15_MEIB, X24_GPMD, X25_POBLACION_DISTRITO) # Variables contextuales adicionales

# Estandarizar datos
datos_std <- scale(vars_clustering)

# Determinar k óptimo
# Método del codo
fviz_nbclust(datos_std, kmeans, method = "wss") +
  labs(title = "Método del Codo")

# Método silhouette  
fviz_nbclust(datos_std, kmeans, method = "silhouette") +
  labs(title = "Método Silhouette")

# Aplicar K-means (ajustar k según métodos anteriores)
set.seed(123)
k_result <- kmeans(datos_std, centers = 6, nstart = 25)

# Visualizar resultados
fviz_cluster(k_result, data = datos_std)

# Agregar clusters a datos originales
datos_final <- datos %>%
  mutate(cluster = as.factor(k_result$cluster))

# Guardar resultados
write.csv(datos_final, "clustering_resultados_reasis.csv", row.names = FALSE)
'''
    
    with open('clustering_kmeans_reasis.R', 'w', encoding='utf-8') as f:
        f.write(script_r)
    
    print(f"\n[BONUS] Script R generado: clustering_kmeans_reasis.R")

def main():
    """Función principal"""
    
    print("CREAR BASE DE DATOS FINAL V5 + EXPORTAR EXCEL PARA R")
    print("=" * 65)
    print("Objetivo: BD limpia con tablas esenciales + Excel para R Studio")
    
    try:
        # 1. Identificar tablas esenciales
        tablas_esenciales, tablas_excluir = identificar_tablas_esenciales()
        
        # 2. Crear BD v5
        total_registros = crear_bd_v5(tablas_esenciales)
        
        # 3. Exportar a Excel
        archivo_excel = exportar_a_excel()
        
        # 4. Generar script R básico
        generar_script_r_basico()
        
        print("\n" + "=" * 65)
        print("[COMPLETADO] BASE DE DATOS FINAL V5 CREADA")
        print(f"[BD] reasis_database_v5.db - {len(tablas_esenciales)} tablas esenciales")
        print(f"[EXCEL] {archivo_excel} - Listo para R Studio") 
        print(f"[SCRIPT] clustering_kmeans_reasis.R - Template básico")
        print(f"[DATOS] {total_registros:,} registros totales preservados")
        print("\n[SIGUIENTE PASO] Abrir Excel en R Studio y seguir PASOS_KMEANS_RSTUDIO.md")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()